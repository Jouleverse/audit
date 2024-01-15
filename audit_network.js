// Jouleverse node audit script
// run:
// sudo docker exec -it jouleverse-mainnet /j/geth --exec 'loadScript("/data/audit_network.js")' attach /data/mainnet/geth.ipc

// revisions:
// 0.2 2024.1.15 evan.j put it to github repo audit/, open for anyone to audit
// ...
// 0.1.2 2023.10.28 evan.j + Menger 比尔盖 miners, - Menger witness
// 0.1.1 2023.10.26 evan.j + Angel witness
// 0.1 2023.10.18 evan.j

// indexed by IP address
const core_nodes = [
	{
		owner: 'JNSDAO',
		type: 'audit',
		ip: '43.134.121.187',
		id: '2379e2c19b8a0e4a76d011b07e41493902c1f274abc5adce3e20fe60f0cabac6'
	},
	{
		owner: 'Jeff',
		type: 'witness',
		ip: '43.136.53.164',
		id: '36d1c18a197fea99e9b55b111b03ab03866367838b3017ae91984e0648e3f677'
	},
	{
		owner: 'Koant',
		type: 'miner',
		ip: '119.29.202.168',
		id: '958a680d9c0fd958b21e5f851539c93b12466a668b37dd4eb3b831f28ac1f199',
		signer: '0xA23e676de107F45A2C873109b6976c1D69b4ad55'
	},
	{
		owner: '谢勇', //稳清活
		type: 'miner',
		ip: '82.157.251.101',
		id: '6f0ef352cc2536d91f0a55efbec480c8e2b76a11fc5c30830167e026327f0a18',
		signer: '0x93196aeEb56fe0F5672d84b8F50C123b5dA50329'
	},
	{
		owner: 'Jacky',
		type: 'miner',
		ip: '47.94.93.119',
		id: 'e88e333abc2dce665fd9c35bef4a0383249b1670955cefac4c582092fa34fbcb',
		signer: '0x28D314d2B00EED89041843d4Cd7b9de91170f37a'
	},
	{
		owner: '一痕',
		type: 'miner',
		ip: '106.75.5.22',
		id: '8118c7cb3f83c1192ed5cdabf3c23798a982faaf2268c5cb2b956dd6d8ecdc2e',
		signer: '0xf7bB10CeDE7E8A0524526577bB4F14390965Cbfa'
	},
	{
		owner: '教链',
		type: 'miner',
		ip: '82.157.210.13',
		id: '61cb546c70e6a470e8ee64c4ff5fbef138d9afe116fb24147636802d6ffac30b',
		signer: '0x85db5D64BD1a2652A75C4A7e12Eeba2f43c57bC4'
	},
	{
		owner: '比尔盖',
		type: 'miner',
		ip: '101.43.165.39',
		id: '32c90f8ee743e588e421c8d374a5ca02ebcabbdc0e6b5b1b912c83185f4522ca',
		signer: '0x1323caeca07e7bd2b5bdb4bc13e67029ad56fa2f'
	},
	{
		owner: 'Menger',
		type: 'miner',
		ip: '62.234.21.37',
		id: '16376be08813c07d06cdf5e073916f97846c67ec08f1f9c3be4ac5d894ab4670',
		signer: '0x3fc084c968e77f264803ef5af09e6d6f05228bea'
	},
	{
		owner: '严光红',
		type: 'miner',
		ip: '106.53.60.230',
		id: 'f92367cc2a9b02c68d6f024b7630bdfa6060d0ce70fc676696633a59eef3ae39',
		signer: '0xcce6cc1ba66c6b9af2c7b20d78155c74ed9aad6f'
	},
	/*{
		owner: 'li17',
		type: 'witness',
		ip: '47.100.5.124',
		id: 'ee1f953cab4741b3147cd3982cd4f3a11686e9dce192640ebbedcbe8814b44ab'
	},*/
	{
		owner: 'li17',
		type: 'miner',
		ip: '47.100.5.124',
		id: 'ffd502a7cebcaad58aff75d9dfde768067d3e78baf31870a7f4debf353107581',
		signer: '0x002ed4ea787fd611f44a8277b5e204aad5c81717'
	},
	{
		owner: '严光红',
		type: 'witness',
		ip: '1.14.111.74',
		id: '65e0dc09479950368c2edaa0d7f3dd30af33ebd0187b31f0ad5df55535905f01'
	},
	{
		owner: '岑云',
		type: 'witness',
		ip: '101.34.72.97',
		id: '0f8d5ded2922bbe42689bd91988f4415d4f81b7a0e22120edde3c30fe8b8b36f'
	},
	{
		owner: '比尔盖',
		type: 'witness',
		ip: '62.234.5.241',
		id: 'b3af9021f81a99afb7ae6a09448973453ddab57db15a9f7cfb8db94171d3920d'
	},
	{
		owner: 'Koant',
		type: 'witness',
		ip: '111.230.23.83',
		id: '6070dfa4ec231c5abeba83114eb8238d69a453e4c17d4aa6706ae320dc0aa922'
	},
	{
		owner: 'Leo',
		type: 'witness',
		ip: '121.40.97.50',
		id: '27c01da9e04d8de57b363054772e417a55706cae39f1e5c20abdffe0c3dbe6b7'
	},
	{
		owner: 'OPEN',
		type: 'witness',
		ip: '124.222.199.61',
		id: '7da1b99acd6bedf5de7ae595aa3676e329b35fc3fa87a93ab0312638549de473'
	},
	{
		owner: '谢勇',
		type: 'witness',
		ip: '120.26.11.88',
		id: 'fb444f8dedff72c18926703b0e9556c99ace3dbcfa442e32b72eb73f147db71f'
	},
	{
		owner: '火星',
		type: 'witness',
		ip: '101.32.170.145',
		id: 'f19522300833eaa81a37030f89aac7169cfcc1ebc32c54ce35518cbcf15722d8'
	},
	{
		owner: 'Angel',
		type: 'witness',
		ip: '115.159.194.193',
		id: '00be8ffef4f441c87e65315a3809f94c98197c1e9b614c65f9ca0edb9d00ccb6'
	},
	{
		owner: '如行',
		type: 'witness',
		ip: '47.102.145.16',
		id: '813c74e91083e2a26b8df6abfe9e58ae188e97739690be8815c89dd5515a066f'
	},
	{
		owner: '老谢',
		type: 'witness',
		ip: '1.14.106.165',
		id: '8e38af25891db9f7e3c5e430d4b220910685830ea33cd7a23cc0b0086474aa9e'
	},
	{
		owner: 'Stars',
		type: 'witness',
		ip: '8.210.106.181',
		id: 'c6d31bf38cd1d1d5c329a08b3a1c3d1d85ed5edd0cfcd9cc5668f1c9ed354342'
	},
	{
		owner: '明海云',
		type: 'witness',
		ip: '43.139.249.74',
		id: 'ea8bcbf9ec92291e54472d3390de4c5231b03661609c46087298b5b451543b02'
	},
	{
		owner: 'gwendol',
		type: 'witness',
		ip: '119.29.222.90',
		id: 'ef9301f5b766aa299c2b7f1a199447346772dcc5c326529ff257710530aae46e'
	},
	{
		owner: '狮子猫',
		type: 'witness',
		ip: '123.206.109.17',
		id: 'e97fcd7f8aed3881648f6d2859ed5da1a589ba9e25c43106c5ff51a14e1994e1'
	},
	{
		owner: 'ucanfilm',
		type: 'witness',
		ip: '47.104.106.73',
		id: 'ceceab24a1f11259f9e9b88a1bd40aca659cf9d4426a08bea4a89110cc7e81e4'
	},
	{
		owner: '元码',
		type: 'witness',
		ip: '47.95.200.73',
		id: 'c6b0f385fd54806b3febf12e4aea8906fad1a175773a4790f9965bdfeb674ce4'
	},
	{
		owner: 'OPEN',
		type: 'miner', //miner*
		ip: '43.142.106.3',
		id: '6cb4e5340a7e5008dfbc3f20f128bc5a6569e343447ecfcd3018304879f28473',
		signer: '0xa2547655F12DF995E74fC4b9E3192De432b8b56f'
	},
	{
		owner: 'Jeff',
		type: 'miner', //miner*
		ip: '47.120.35.41',
		id: '58871675d4f24d7c916b4c3ccad303b3b862abfe125b1650b0177bd8be09e896',
		signer: '0x0ac52a05a4f87404b03dd58a7ac1427429522222'
	},
	{
		owner: 'bonny',
		type: 'witness',
		ip: '123.207.42.3',
		id: '846e5a80a3ffa352be827443689bcae87fa01d47fd00edaab2b103c0d0b5a80d'
	},
	{
		owner: 'Mr.',
		type: 'witness',
		ip: '43.136.53.179',
		id: 'f7f5b821da9e90caad7979373188f9488496800c94746b1955e8aaabdca0fc6d'
	},
	{
		owner: 'cijin',
		type: 'witness',
		ip: '106.53.39.89',
		id: '73741045125ed13335ab0440857a745473d43edc5bd5667f92f44e021aa9bf01'
	},
]

const id_nodes = {} //nodes indexed by id
const signers = {} //miner nodes indexed by lc(signer address)
for (const node of core_nodes) {
	id_nodes[node.id] = node
	if (node.type == 'miner') {
		signers[node.signer.toLowerCase()] = node
	}
}

const stat = clique.status()
for (const [addr, n] of Object.entries(stat.sealerActivity)) {
	const signer = signers[addr.toLowerCase()]
	signer.block_rate = n/stat.numBlocks
}

const peers = admin.peers
for (const peer of peers) {
	const ip = peer.enode.match(/enode:\/\/\w+@([\d\.]+):\d+/)[1]
	const id = peer.id
	const name = peer.name

	if (id_nodes[id]) {
		const node = id_nodes[id]
		if(node.type != 'miner') {
			node.block_rate = 0
		}

		if (ip !== node.ip) {
			node.status = 'error'
			node.error = 'IP mismatch: peer ip = ' + ip
		} else {
			node.name = name
			node.status = 'connected'
		}
	}
}

//output report

console.log('Jouleverese Network Audit Report')
console.log('===============================================')
console.log('Report Time:', Date())
console.log('------------- blockchain status ---------------')

const last_block_n = eth.blockNumber
const last_block = eth.getBlock(last_block_n)
const last_block_t = Date(last_block.timestamp)

const current = Date.now() / 1000
const diff_t = current - last_block.timestamp
if (diff_t < 60) {
	console.log('Blockchain Status: 🟢')
} else {
	console.log('Blockchain Status: 🔴')
}

console.log('Latest Block Height:', last_block_n)
console.log('Latest Block Time:', last_block_t)

// count connected nodes
var count = count_miner = count_witness = 0;
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.status == 'connected' || (node.type == 'miner' && node.block_rate > 0))  {
		count++
		if (node.type == 'miner') {
			count_miner++
		} else {
			count_witness++
		}
	}
}
// note: include the audit node itself, so +1
console.log('Network Size: ', count + 1, ' nodes (', count_miner, ' miners, ', count_witness + 1, ' witnesses+miner*s)')

console.log('---------------- nodes status -----------------')

//print this audit node itself first
const node = core_nodes[0]
console.log(node.type, node.ip, '✅', 'connected', node.owner, '0')

const report = function(node) {
	node.status = node.status ? node.status : 'disconnected'
	node.audit = (node.status == 'connected') ? '✅':'❌'
	//console.log(node.type, node.ip, node.audit, node.status, node.owner, node.id, node.block_rate)
	console.log(node.type, node.ip, node.audit, node.status, node.owner, node.block_rate)
}

// first scan, miner
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'miner')
		report(node)
}

// second scan, miner* (miner ready candidate - after PoS, before voting)
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'miner*')
		report(node)
}
//
// third scan, connected witness
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'witness' && node.status)
		report(node)
}

// fourth scan, disconnected witness
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'witness' && !node.status)
		report(node)
}
