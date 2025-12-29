pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

contract AuditPoints is Ownable2Step, Pausable {
    enum NodeType { MINER, WITNESS }

    struct DailyRecord {
        uint64 blockTimestamp;
        uint32 coreId;
        uint32 date;
        uint16 points;
        NodeType nodeType;
        bool exists;
        bool liveness;
        bool checkin;
    }

    address public operator;
    // 批量大小上限（可配置）：避免超长批次导致 gas 过高或意外风险
    uint256 public maxBatchSize = 200;
    

    mapping(uint32 => mapping(NodeType => mapping(uint32 => DailyRecord))) private records; // coreId => nodeType => date => DailyRecord

    // 记录事件
    event DailyRecorded(
        uint32 indexed coreId,
        uint32 indexed date,
        NodeType indexed nodeType,
        bool liveness,
        bool checkin,
        uint256 points
    );
    event DailyOverridden(
        uint32 indexed coreId,
        uint32 indexed date,
        NodeType indexed nodeType,
        bool oldLiveness,
        bool newLiveness,
        bool oldCheckin,
        bool newCheckin,
        uint256 oldPoints,
        uint256 newPoints
    );
    event OperatorUpdated(address indexed previousOperator, address indexed newOperator);
    event MaxBatchSizeUpdated(uint256 oldValue, uint256 newValue);
    

    modifier onlyOperator() {
        require(msg.sender == operator, "not operator");
        _;
    }

    constructor(address initialOperator) Ownable(msg.sender) Ownable2Step() Pausable() {
        operator = initialOperator == address(0) ? msg.sender : initialOperator;
        emit OperatorUpdated(address(0), operator);
    }

    function setOperator(address newOperator) external onlyOwner {
        require(newOperator != address(0), "zero address");
        address prev = operator;
        operator = newOperator;
        emit OperatorUpdated(prev, newOperator);
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    // 配置：批量大小上限
    function setMaxBatchSize(uint256 newSize) external onlyOwner {
        require(newSize > 0 && newSize <= 1000, "bad maxBatchSize");
        uint256 old = maxBatchSize;
        maxBatchSize = newSize;
        emit MaxBatchSizeUpdated(old, newSize);
    }

    

    function getDaily(uint32 coreId, NodeType nodeType, uint32 date)
        external
        view
        returns (
            bool exists,
            uint32 storedCoreId,
            NodeType storedNodeType,
            bool liveness,
            bool checkin,
            uint256 points,
            uint32 storedDate,
            uint256 blockTimestamp
        )
    {
        DailyRecord storage r = records[coreId][nodeType][date];
        return (r.exists, r.coreId, r.nodeType, r.liveness, r.checkin, r.points, r.date, r.blockTimestamp);
    }

    // 日期校验：拆到独立函数以减少调用方局部变量并避免 "stack too deep"
    function _validateDate(uint32 date) internal pure {
        require(date >= 20000101 && date <= 99991231, "bad date");
        uint32 mm = (date / 100) % 100;
        uint32 dd = date % 100;
        require(mm >= 1 && mm <= 12 && dd >= 1 && dd <= 31, "bad date");
    }
    function _checkNoDuplicatePairs(
        uint32[] calldata coreIds,
        NodeType[] calldata nodeTypes,
        uint32[] calldata dates
    ) internal pure {
        uint256 len = coreIds.length;
        for (uint256 i = 0; i < len; i++) {
            uint32 cid = coreIds[i];
            NodeType nt = nodeTypes[i];
            uint32 d = dates[i];
            for (uint256 j = i + 1; j < len; j++) {
                if (coreIds[j] == cid && nodeTypes[j] == nt && dates[j] == d) {
                    revert("duplicate in batch");
                }
            }
        }
    }

    // 内部：批处理单项，进一步缩短 recordBatch 的局部变量生命周期，缓解栈压力
    function _recordBatchItem(
        uint32 coreId,
        uint32 date,
        NodeType nodeType,
        bool liveness,
        bool checkin,
        uint256 points
    ) internal {
        _validateDate(date);
        _recordDaily(coreId, date, nodeType, liveness, checkin, points);
    }

    // 记录每日
    function recordDaily(
        uint32 coreId,
        uint32 date,
        NodeType nodeType,
        bool liveness,
        bool checkin,
        uint256 points
    ) external onlyOperator whenNotPaused returns (bool updated) {
        // 日期校验
        _validateDate(date);
        require(nodeType == NodeType.MINER || nodeType == NodeType.WITNESS, "invalid nodeType");
        require(points <= 65535, "points too large");
        return _recordDaily(
            coreId,
            date,
            nodeType,
            liveness,
            checkin,
            points
        );
    }

    // 内部：记录每日数据（标准实现）
    function _recordDaily(
        uint32 coreId,
        uint32 date,
        NodeType nodeType,
        bool liveness,
        bool checkin,
        uint256 points
    ) internal returns (bool updated) {
        DailyRecord storage r = records[coreId][nodeType][date];
        if (r.exists) {
            if (
                r.nodeType == nodeType &&
                r.liveness == liveness &&
                r.checkin == checkin &&
                r.points == points
            ) {
                return false;
            }
            emit DailyOverridden(
                coreId,
                date,
                nodeType,
                r.liveness,
                liveness,
                r.checkin,
                checkin,
                r.points,
                points
            );
            r.coreId = coreId;
            r.nodeType = nodeType;
            r.liveness = liveness;
            r.checkin = checkin;
            r.points = uint16(points);
            r.blockTimestamp = uint64(block.timestamp);
            return true;
        } else {
            r.exists = true;
            r.coreId = coreId;
            r.nodeType = nodeType;
            r.liveness = liveness;
            r.checkin = checkin;
            r.points = uint16(points);
            r.date = date;
            r.blockTimestamp = uint64(block.timestamp);
            emit DailyRecorded(coreId, date, nodeType, liveness, checkin, points);
            return true;
        }
    }

    // 批量记录
    function recordBatch(
        uint32[] calldata coreIds,
        uint32[] calldata dates,
        NodeType[] calldata nodeTypes,
        bool[] calldata livenesses,
        bool[] calldata checkins,
        uint256[] calldata points
    ) external onlyOperator whenNotPaused {
        require(coreIds.length <= maxBatchSize, "batch too large");
        require(
            coreIds.length == dates.length &&
                dates.length == nodeTypes.length &&
                nodeTypes.length == livenesses.length &&
                livenesses.length == checkins.length &&
                checkins.length == points.length,
            "length mismatch"
        );
        _checkNoDuplicatePairs(coreIds, nodeTypes, dates);

        for (uint256 i = 0; i < coreIds.length;) {
            require(nodeTypes[i] == NodeType.MINER || nodeTypes[i] == NodeType.WITNESS, "invalid nodeType");
            _validateDate(dates[i]);
            require(points[i] <= 65535, "points too large");
            _recordDaily(
                coreIds[i],
                dates[i],
                nodeTypes[i],
                livenesses[i],
                checkins[i],
                points[i]
            );
            unchecked { i++; }
        }
    }

    

    // 查询：每日记录详细信息
    function getDailyBreakdown(uint32 coreId, NodeType nodeType, uint32 date)
        external
        view
        returns (bool liveness, bool checkin, uint256 points)
    {
        DailyRecord storage r = records[coreId][nodeType][date];
        return (r.liveness, r.checkin, r.points);
    }

    // 查询一个coreId在某个日期的所有节点记录
    function getCoreDailyRecords(uint32 coreId, uint32 date)
        external
        view
        returns (
            bool minerExists,
            bool minerLiveness,
            bool minerCheckin,
            uint256 minerPoints,
            bool witnessExists,
            bool witnessLiveness,
            bool witnessCheckin,
            uint256 witnessPoints
        )
    {
        DailyRecord storage minerRecord = records[coreId][NodeType.MINER][date];
        DailyRecord storage witnessRecord = records[coreId][NodeType.WITNESS][date];

        return (
            minerRecord.exists,
            minerRecord.liveness,
            minerRecord.checkin,
            minerRecord.points,
            witnessRecord.exists,
            witnessRecord.liveness,
            witnessRecord.checkin,
            witnessRecord.points
        );
    }
}
