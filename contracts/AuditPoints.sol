pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/access/Ownable2Step.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract AuditPoints is Ownable2Step, Pausable {
    struct DailyRecord {
        bool exists;
        bool liveness;
        bool checkin;
        uint16 pointsBP;
        // 角色积分拆分：记账(miner)与见证(witness)
        uint16 minerBP;
        uint16 witnessBP;
        uint32 date;
        uint256 blockTimestamp;
    }

    address public operator;
    // 批量大小上限（可配置）：避免超长批次导致 gas 过高或意外风险
    uint256 public maxBatchSize = 200;
    // 每月索引容量上限（可配置）：防止月度索引无限增长
    uint256 public maxMonthIndexSize = 10000;

    mapping(uint256 => mapping(uint32 => DailyRecord)) private records;
    mapping(uint256 => mapping(uint32 => uint256)) private monthlyPoints;
    // 索引每月参与积分的 tokenId；用于月度明细查询（不移除，0 分可由调用方过滤）
    mapping(uint32 => uint256[]) private monthIndex;
    // 标记是否已加入索引，避免重复加入
    mapping(uint256 => mapping(uint32 => bool)) private monthIndexed;

    // 记录事件（包含角色积分拆分）
    event DailyRecorded(
        uint256 indexed tokenId,
        uint32 indexed date,
        bool liveness,
        bool checkin,
        uint16 minerBP,
        uint16 witnessBP,
        uint16 pointsBP,
        uint32 indexed monthKey
    );
    event DailyOverridden(
        uint256 indexed tokenId,
        uint32 indexed date,
        uint16 oldMinerBP,
        uint16 oldWitnessBP,
        uint16 newMinerBP,
        uint16 newWitnessBP,
        uint16 oldPointsBP,
        uint16 newPointsBP,
        uint32 indexed monthKey
    );
    event OperatorUpdated(address indexed previousOperator, address indexed newOperator);
    event MaxBatchSizeUpdated(uint256 oldValue, uint256 newValue);
    event MaxMonthIndexSizeUpdated(uint256 oldValue, uint256 newValue);

    modifier onlyOperator() {
        require(msg.sender == operator, "not operator");
        _;
    }

    constructor(address initialOperator) Ownable(msg.sender) {
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
        require(newSize > 0 && newSize <= 10000, "bad maxBatchSize");
        uint256 old = maxBatchSize;
        maxBatchSize = newSize;
        emit MaxBatchSizeUpdated(old, newSize);
    }

    // 配置：每月索引容量上限
    function setMaxMonthIndexSize(uint256 newSize) external onlyOwner {
        require(newSize > 0 && newSize <= 1000000, "bad maxMonthIndexSize");
        uint256 old = maxMonthIndexSize;
        maxMonthIndexSize = newSize;
        emit MaxMonthIndexSizeUpdated(old, newSize);
    }

    function getDaily(uint256 tokenId, uint32 date)
        external
        view
        returns (
            bool exists,
            bool liveness,
            bool checkin,
            uint16 pointsBP,
            uint32 storedDate,
            uint256 blockTimestamp
        )
    {
        DailyRecord storage r = records[tokenId][date];
        return (r.exists, r.liveness, r.checkin, r.pointsBP, r.date, r.blockTimestamp);
    }

    function getMonthlyPoints(uint256 tokenId, uint32 monthKey) external view returns (uint256) {
        return monthlyPoints[tokenId][monthKey];
    }

    function _monthKey(uint32 date) internal pure returns (uint32) {
        uint32 yyyy = date / 10000;
        uint32 mm = (date / 100) % 100;
        return yyyy * 100 + mm;
    }

    // 日期校验：拆到独立函数以减少调用方局部变量并避免 "stack too deep"
    function _validateDate(uint32 date) internal pure {
        require(date >= 20000101 && date <= 99991231, "bad date");
        uint32 mm = (date / 100) % 100;
        uint32 dd = date % 100;
        require(mm >= 1 && mm <= 12 && dd >= 1 && dd <= 31, "bad date");
    }

    // 批次去重校验：禁止同一批次中重复的 (tokenId, date) 对，避免误覆盖
    function _checkNoDuplicatePairs(uint256[] calldata tokenIds, uint32[] calldata dates) internal pure {
        uint256 len = tokenIds.length;
        for (uint256 i = 0; i < len; i++) {
            uint256 tid = tokenIds[i];
            uint32 d = dates[i];
            for (uint256 j = i + 1; j < len; j++) {
                if (tokenIds[j] == tid && dates[j] == d) {
                    revert("duplicate in batch");
                }
            }
        }
    }

    // 内部：批处理单项，进一步缩短 recordBatch 的局部变量生命周期，缓解栈压力
    function _recordBatchItem(
        uint256 tokenId,
        uint32 date,
        bool liveness,
        bool checkin,
        uint16 minerBP,
        uint16 witnessBP
    ) internal {
        _validateDate(date);
        require(minerBP <= 100 && witnessBP <= 100, "BP role limit");
        require(minerBP + witnessBP <= 200, "BP sum limit");
        _recordDaily(tokenId, date, liveness, checkin, minerBP, witnessBP, _monthKey(date));
    }

    // 记录每日：支持传入角色积分拆分
    function recordDaily(
        uint256 tokenId,
        uint32 date,
        bool liveness,
        bool checkin,
        uint16 minerBP,
        uint16 witnessBP
    ) external onlyOperator whenNotPaused returns (bool updated) {
        // 日期与 BP 上限校验
        _validateDate(date);
        require(minerBP <= 100 && witnessBP <= 100, "BP role limit");
        require(minerBP + witnessBP <= 200, "BP sum limit");
        return _recordDaily(
            tokenId,
            date,
            liveness,
            checkin,
            minerBP,
            witnessBP,
            _monthKey(date)
        );
    }

    // 内部：记录含角色积分拆分（标准实现）
    function _recordDaily(
        uint256 tokenId,
        uint32 date,
        bool liveness,
        bool checkin,
        uint16 minerBP,
        uint16 witnessBP,
        uint32 monthKey
    ) internal returns (bool updated) {
        DailyRecord storage r = records[tokenId][date];
        uint16 pointsBP = minerBP + witnessBP;
        uint256 prev = monthlyPoints[tokenId][monthKey];
        if (r.exists) {
            if (
                r.pointsBP == pointsBP &&
                r.liveness == liveness &&
                r.checkin == checkin &&
                r.minerBP == minerBP &&
                r.witnessBP == witnessBP
            ) {
                return false;
            }
            monthlyPoints[tokenId][monthKey] = prev + pointsBP - r.pointsBP;
            uint256 newVal = monthlyPoints[tokenId][monthKey];
            if (prev == 0 && newVal > 0 && !monthIndexed[tokenId][monthKey]) {
                require(monthIndex[monthKey].length < maxMonthIndexSize, "month index full");
                monthIndex[monthKey].push(tokenId);
                monthIndexed[tokenId][monthKey] = true;
            }
            emit DailyOverridden(
                tokenId,
                date,
                r.minerBP,
                r.witnessBP,
                minerBP,
                witnessBP,
                r.pointsBP,
                pointsBP,
                monthKey
            );
            r.liveness = liveness;
            r.checkin = checkin;
            r.pointsBP = pointsBP;
            r.minerBP = minerBP;
            r.witnessBP = witnessBP;
            r.blockTimestamp = block.timestamp;
            return true;
        } else {
            r.exists = true;
            r.liveness = liveness;
            r.checkin = checkin;
            r.pointsBP = pointsBP;
            r.minerBP = minerBP;
            r.witnessBP = witnessBP;
            r.date = date;
            r.blockTimestamp = block.timestamp;
            monthlyPoints[tokenId][monthKey] += pointsBP;
            uint256 newVal = monthlyPoints[tokenId][monthKey];
            if (prev == 0 && newVal > 0 && !monthIndexed[tokenId][monthKey]) {
                require(monthIndex[monthKey].length < maxMonthIndexSize, "month index full");
                monthIndex[monthKey].push(tokenId);
                monthIndexed[tokenId][monthKey] = true;
            }
            emit DailyRecorded(tokenId, date, liveness, checkin, minerBP, witnessBP, pointsBP, monthKey);
            return true;
        }
    }

    // 批量记录：角色拆分积分
    function recordBatch(
        uint256[] calldata tokenIds,
        uint32[] calldata dates,
        bool[] calldata livenesses,
        bool[] calldata checkins,
        uint16[] calldata minerBPs,
        uint16[] calldata witnessBPs
    ) external onlyOperator whenNotPaused {
        require(tokenIds.length <= maxBatchSize, "batch too large");
        require(
            tokenIds.length == dates.length &&
                dates.length == livenesses.length &&
                livenesses.length == checkins.length &&
                checkins.length == minerBPs.length &&
                minerBPs.length == witnessBPs.length,
            "length mismatch"
        );
        _checkNoDuplicatePairs(tokenIds, dates);
        for (uint256 i = 0; i < tokenIds.length;) {
            _recordBatchItem(
                tokenIds[i],
                dates[i],
                livenesses[i],
                checkins[i],
                minerBPs[i],
                witnessBPs[i]
            );
            unchecked { i++; }
        }
    }

    // 月度积分明细：返回该月涉及的 tokenId 及其积分；可能包含积分为 0 的条目（调用方可过滤）
    function getMonthlyDetail(uint32 monthKey)
        external
        view
        returns (uint256[] memory tokenIds, uint256[] memory points)
    {
        uint256 len = monthIndex[monthKey].length;
        tokenIds = new uint256[](len);
        points = new uint256[](len);
        for (uint256 i = 0; i < len; i++) {
            uint256 tid = monthIndex[monthKey][i];
            tokenIds[i] = tid;
            points[i] = monthlyPoints[tid][monthKey];
        }
    }

    // 月度索引计数：用于前端分页或合约端分批读取
    function getMonthlyDetailCount(uint32 monthKey) external view returns (uint256) {
        return monthIndex[monthKey].length;
    }

    // 月度分页查询：返回从 offset 开始的最多 limit 条（limit 可大于剩余条数）
    function getMonthlyDetailPaged(uint32 monthKey, uint256 offset, uint256 limit)
        external
        view
        returns (uint256[] memory tokenIds, uint256[] memory points)
    {
        uint256 total = monthIndex[monthKey].length;
        require(offset <= total, "offset out of range");
        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }
        uint256 len = end > offset ? end - offset : 0;
        tokenIds = new uint256[](len);
        points = new uint256[](len);
        for (uint256 i = 0; i < len; i++) {
            uint256 tid = monthIndex[monthKey][offset + i];
            tokenIds[i] = tid;
            points[i] = monthlyPoints[tid][monthKey];
        }
    }

    // 查询：每日积分角色拆分
    function getDailyBreakdown(uint256 tokenId, uint32 date)
        external
        view
        returns (uint16 minerBP, uint16 witnessBP)
    {
        DailyRecord storage r = records[tokenId][date];
        return (r.minerBP, r.witnessBP);
    }
}