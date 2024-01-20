// Jouleverse node audit script
// run:
// sudo docker exec -it jouleverse-mainnet /j/geth --exec 'loadScript("/data/audit_network.js")' attach /data/mainnet/geth.ipc

// indexed by IP address
const core_nodes = [
	{
		owner: 'JNSDAO',
		type: 'witness',
		ip: '43.134.121.187', // bootnode.jnsdao.com
		id: '2379e2c19b8a0e4a76d011b07e41493902c1f274abc5adce3e20fe60f0cabac6',
		enode: 'enode://19dc6b15744e8ad73f860d6ca7bf7b1acf37497ef8a720a88d64449ec837af460535fcf01662907aaece6bde0c2ff539a9d79e353d043769134666a1586fa4e0@43.134.121.187:30311'
	},
	{
		owner: 'Jeff',
		type: 'witness',
		ip: '43.136.53.164', // bootnode-jeff.jnsdao.com
		id: '36d1c18a197fea99e9b55b111b03ab03866367838b3017ae91984e0648e3f677',
		enode: 'enode://f3e4e524d89b4cdb9ee390d9485cee4d6a5e9a260f5673cab118505cc3e69fe8365bc00434222d27fe4082ca798b13ad8e7e139d1315f635fd0e46dbe96fa809@43.136.53.164:30311'
	},
	{
		owner: 'Koant',
		type: 'miner',
		ip: '119.29.202.168',
		id: '958a680d9c0fd958b21e5f851539c93b12466a668b37dd4eb3b831f28ac1f199',
		signer: '0xA23e676de107F45A2C873109b6976c1D69b4ad55',
		enode: 'enode://dbf6ba9d689929e1f8824d53b0e7bd62ceeaff32d65821de5054dd2b48b7701458fb537345c1842c428d5e8918775cffef411e74b073c5d1ff815e78d13270fb@119.29.202.168:30311'
	},
	{
		owner: '谢勇', //稳清活
		type: 'miner',
		ip: '82.157.251.101',
		id: '6f0ef352cc2536d91f0a55efbec480c8e2b76a11fc5c30830167e026327f0a18',
		signer: '0x93196aeEb56fe0F5672d84b8F50C123b5dA50329',
		enode: 'enode://c43fa0ea62dfc0e09906f67a8b730918cbe567a3f53322470780ecdc569efda1a2dd9e4707ac65e3b558e9bf8a025a22da33b1ad08211290211b8c5ed0ed1671@82.157.251.101:30311'
	},
	{
		owner: 'Jacky',
		type: 'miner',
		ip: '47.94.93.119',
		id: 'e88e333abc2dce665fd9c35bef4a0383249b1670955cefac4c582092fa34fbcb',
		signer: '0x28D314d2B00EED89041843d4Cd7b9de91170f37a',
		enode: 'enode://be96ad65107a3d520943f761d00a79a6e08bd4acc5b008b58ff8406761e5ca7e923bcb310654089b1ab364579f70ebe042f2baf9c9adbfa8482052f31c6766f1@47.94.93.119:30311'
	},
	{
		owner: '一痕',
		type: 'miner',
		ip: '106.75.5.22',
		id: '8118c7cb3f83c1192ed5cdabf3c23798a982faaf2268c5cb2b956dd6d8ecdc2e',
		signer: '0xf7bB10CeDE7E8A0524526577bB4F14390965Cbfa',
		enode: 'enode://91ccd999fe750e950d722f71279c678cae4abdcadfe18e18e2f785871648d386c3db8d2a39fcad49488f6daea4b5d41d3d7cbbb979c31299e9387e0c9d867a37@106.75.5.22:30311'
	},
	{
		owner: '教链',
		type: 'miner',
		ip: '82.157.210.13',
		id: '61cb546c70e6a470e8ee64c4ff5fbef138d9afe116fb24147636802d6ffac30b',
		signer: '0x85db5D64BD1a2652A75C4A7e12Eeba2f43c57bC4',
		enode: 'enode://d667d09c38706d40fa1c15cde8dc28c117087cdf55d41d402d70b0817636c6f65e6a6463e81ab178ad9a896ea93c37b479a01ff19dfe13cd4276ea2c64575c76@81.68.150.141:30311'
	},
	{
		owner: '比尔盖',
		type: 'miner',
		ip: '101.43.165.39',
		id: '32c90f8ee743e588e421c8d374a5ca02ebcabbdc0e6b5b1b912c83185f4522ca',
		signer: '0x1323caeca07e7bd2b5bdb4bc13e67029ad56fa2f',
		enode: 'enode://d33540329429582a6c10c917f66103a8e9ce97da24c34bf14d5fd211a8eb4640c6d5ac1a30a764cebd872e6966c04750912726359534a9d4fba5d78c837f4bf0@101.43.165.39:30311'
	},
	{
		owner: 'Menger',
		type: 'miner',
		ip: '62.234.21.37',
		id: '16376be08813c07d06cdf5e073916f97846c67ec08f1f9c3be4ac5d894ab4670',
		signer: '0x3fc084c968e77f264803ef5af09e6d6f05228bea',
		enode: 'enode://72ced57bb2a447947d7bf6378ee927fb04954eba69063571bec3cd3e3cf8d5e660ffb3e62a2cf073045f949a592b2a2c66a1d5bf700a00f069531239749a8382@62.234.21.37:30311'
	},
	{
		owner: '严光红',
		type: 'miner',
		ip: '106.53.60.230',
		id: 'f92367cc2a9b02c68d6f024b7630bdfa6060d0ce70fc676696633a59eef3ae39',
		signer: '0xcce6cc1ba66c6b9af2c7b20d78155c74ed9aad6f',
		enode: 'enode://94b45bc3705c8abebeda0ee9b31a76188b59c0c69397362e96accd39b15a56668775204d4f2e3e7ddb2b14df0b640b5bb9cd4dcb60c252ef80268f1af815f623@106.53.60.230:30311'
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
		signer: '0x002ed4ea787fd611f44a8277b5e204aad5c81717',
		enode: 'enode://b7055440d2792887e10ca12192d5d30200a4d9352d9de560732589014e26e5b6c587c5ae201441597795f33b2af6afecadb31193bf6f467024e3144ba40f6d2b@47.100.5.124:30311'
	},
	{
		owner: '严光红',
		type: 'witness',
		ip: '1.14.111.74', // bootnode-ygh.jnsdao.com
		id: '65e0dc09479950368c2edaa0d7f3dd30af33ebd0187b31f0ad5df55535905f01',
		enode: 'enode://b3eca38a3d18a789a0ca4e0e871c77fbf98fbe82cb8ed577895be8be14599abd07df88fe5fcf5fa11a63843b25bbc69b28da9a68bc0fcf42b01583329d4e0006@1.14.111.74:30311'
	},
	{
		owner: '岑云',
		type: 'witness',
		ip: '101.34.72.97',
		id: '0f8d5ded2922bbe42689bd91988f4415d4f81b7a0e22120edde3c30fe8b8b36f',
		enode: 'enode://5ac5fa3a878b63f911314311a1804732e63e7fd6dabc8d34f5dd033322d479cc5be4764d05eadea7ca70e83910129c5898d163d7454916b4a2738f510cd77b01@101.34.72.97:30311'
	},
	{
		owner: '比尔盖',
		type: 'witness',
		ip: '62.234.5.241', // bootnode-biergai.jnsdao.com
		id: 'b3af9021f81a99afb7ae6a09448973453ddab57db15a9f7cfb8db94171d3920d',
		enode: 'enode://1c4979289156cf90ac190bd6a5f6841886c421ff017dd0d842d8e847973d751f9e13c90e880081c3ba8df5bc572969266c25dac98fc60da68ce6857dcf39da23@62.234.5.241:30311'
	},
	{
		owner: 'Koant',
		type: 'witness',
		ip: '111.230.23.83', // bootnode-koant.jnsdao.com
		id: '6070dfa4ec231c5abeba83114eb8238d69a453e4c17d4aa6706ae320dc0aa922',
		enode: 'enode://6fd8e9c18272d4fb523beb44bfe9fa4d85107f530ab60a324b5e1aff23ef7f57f7bb6c4959d0b37d3645e2583c6492ec8b4125e30d97aeb10b810f29b9de2cdd@111.230.23.83:30311'
	},
	{
		owner: 'Leo',
		type: 'witness',
		ip: '121.40.97.50',
		id: '27c01da9e04d8de57b363054772e417a55706cae39f1e5c20abdffe0c3dbe6b7',
		enode: 'enode://aac8963e6ed260be67d83275faed5cbda6880ecec31abc7e223932c12b5b131d81edc4efb7bc977572afefd6cd3dcd3b4903b44689ca57f8a4f80e935106dacd@121.40.97.50:30311'
	},
	{
		owner: 'OPEN',
		type: 'witness',
		ip: '124.222.199.61', // bootnode-open.jnsdao.com
		id: '7da1b99acd6bedf5de7ae595aa3676e329b35fc3fa87a93ab0312638549de473',
		enode: 'enode://0a8b5aa7210ada01d9919e4f1a19860a2946f6e54ae2e0fb8c7e1b7e5482546c478260d284255da92d95d579cffd6ce06ec0bf520b7e4e71876a1efa68f7674d@124.222.199.61:30311'
	},
	{
		owner: '谢勇',
		type: 'witness',
		ip: '120.26.11.88', // bootnode-wenqinghuo.jnsdao.com
		id: 'cc99492e1e2d2f9b125b8e1faae3c8d0d47eeadc63ac3ac7e58b0767bfde2726',
		enode: 'enode://b7908693bf2268db08c4fa868d8ea88298e9844a5892681eb63cb4a1a4b254356b5936f6a006dcc709212043b8da325ab72beb3cc2c26cc98843dc301914c961@120.26.11.88:30311'
	},
	{
		owner: '火星',
		type: 'witness',
		ip: '101.32.170.145',
		id: '9bfbcdd542f8f7af28a9b3c50dc5dbd1bff8085311b9b216716a7106880ad6f2',
		enode: 'enode://5fe23cce534e7a49a0a6f79203fec02e84391ada79cf8fc0dc8ef2901ddc5620beea52dbab009c6ecb2bdc127ae084a252ffbf5c9221f733d096f346d3f25cf9@101.32.170.145:30311'
	},
	{
		owner: 'Angel',
		type: 'witness',
		ip: '115.159.194.193',
		id: '00be8ffef4f441c87e65315a3809f94c98197c1e9b614c65f9ca0edb9d00ccb6',
		enode: 'enode://7d757a706f1c662f63134bfd7439efafb62f11328d0904a3b38677bb27e50632bec061c27e7cbda9eebca08b8040ae96bb04b2de14fc3d9bcb979a8e6d476bfc@115.159.194.193:30311'
	},
	/*{
		owner: '如行',
		type: 'witness',
		ip: '47.102.145.16',
		id: '813c74e91083e2a26b8df6abfe9e58ae188e97739690be8815c89dd5515a066f'
	},*/
	{
		owner: '老谢',
		type: 'witness',
		ip: '1.14.106.165',
		id: '8e38af25891db9f7e3c5e430d4b220910685830ea33cd7a23cc0b0086474aa9e',
		enode: 'enode://8d820aefee882f7767be1035cbe018200c4daf9030482aa5f6b25665b78b6ee31f4e041d9b439e4ea6c0a7cce5cd76b6fffa76f0bb4229ee6751d52947065dfe@1.14.106.165:30311'
	},
	{
		owner: 'Stars',
		type: 'witness',
		ip: '8.210.106.181',
		id: 'c6d31bf38cd1d1d5c329a08b3a1c3d1d85ed5edd0cfcd9cc5668f1c9ed354342',
		enode: 'enode://b750ce05ff791ff659481b7ede44338478f4eb816573c9e71aa892df085bab2841c8271c0c534c290c0348d3fd7468ad3df888dd7a286e298ab0d1037295f823@8.210.106.181:30311'
	},
	{
		owner: '明海云',
		type: 'witness',
		ip: '43.139.249.74',
		id: 'ea8bcbf9ec92291e54472d3390de4c5231b03661609c46087298b5b451543b02',
		enode: 'enode://256ec7a9357908270c02c39bec8ba1852a71a4892c9fab95de89fe1a78a6839504f2b4ab1c12e877b8f7d3f6646fbc816ff56d707cc56d49de6158e4cc39ba93@43.139.249.74:30311'
	},
	{
		owner: 'gwendol',
		type: 'witness',
		ip: '119.29.222.90',
		id: 'ef9301f5b766aa299c2b7f1a199447346772dcc5c326529ff257710530aae46e',
		enode: 'enode://1dc186a0c401bcfc560d7188810ce3290bd7a05a76bc0fc9237a06042576cf1f1c356f8fb556da234950b88c21c08ff2ba70ab4e58564a74ea46a24511ccff7c@119.29.222.90:30311'
	},
	{
		owner: '狮子猫',
		type: 'witness',
		ip: '123.206.109.17',
		id: 'e97fcd7f8aed3881648f6d2859ed5da1a589ba9e25c43106c5ff51a14e1994e1',
		enode: 'enode://efc01ff491d277c73394095de99e8d62d25b5b981e03a4de5419d9bbf5bf6dd1ef6b89e169d376970c1a7af4fc73c90fd2d34b954f02c5367e0150911944cc41@123.206.109.17:30311'
	},
	/*{
		owner: 'ucanfilm',
		type: 'witness',
		ip: '47.104.106.73',
		id: 'ceceab24a1f11259f9e9b88a1bd40aca659cf9d4426a08bea4a89110cc7e81e4'
	},*/
	{
		owner: '元码',
		type: 'witness',
		ip: '47.95.200.73',
		id: 'c6b0f385fd54806b3febf12e4aea8906fad1a175773a4790f9965bdfeb674ce4',
		enode: 'enode://bba7d137900d93f0b2b62ebcb7917055e47c77b34bba2784008b841561b81fa331a84d45f1fa227f49b18500deb9a3b324a18a7761372f8e9ab1f285a590f146@47.95.200.73:30311'
	},
	{
		owner: 'OPEN',
		type: 'miner', //miner*
		ip: '43.142.106.3',
		id: '6cb4e5340a7e5008dfbc3f20f128bc5a6569e343447ecfcd3018304879f28473',
		signer: '0xa2547655F12DF995E74fC4b9E3192De432b8b56f',
		enode: 'enode://73cd7670e483a1d7238cf0bdd557236ea554fa343e9bed85e92f2e45cef859f3a1f4a0f7571a18f54090a206fd62132ded8d3327310a2564374cc01ecad65314@43.142.106.3:30311'
	},
	{
		owner: 'Jeff',
		type: 'miner', //miner*
		ip: '47.120.35.41',
		id: '58871675d4f24d7c916b4c3ccad303b3b862abfe125b1650b0177bd8be09e896',
		signer: '0x0ac52a05a4f87404b03dd58a7ac1427429522222',
		enode: 'enode://db1d084eaf12722b04600084a9bd5dcdbbff89facedff931629354ac396acf3564082fbae5a933f1bf4332a174bf9374941dc1caa1527f32c909589a26796014@47.120.35.41:30311'
	},
	{
		owner: 'bonny',
		type: 'witness',
		ip: '123.207.42.3',
		id: '846e5a80a3ffa352be827443689bcae87fa01d47fd00edaab2b103c0d0b5a80d',
		enode: 'enode://3732ea7ef0e0d52f83e67136a09bfc82dbcdc53ec5fab8fb3d540f55e6a966fa76908fcd06103a0fa31fe140d2fd52ca1782e5e8c0ea8b59d8bae5d650e3f93d@123.207.42.3:30311'
	},
	{
		owner: 'Mr.',
		type: 'witness',
		ip: '43.136.53.179',
		id: 'f7f5b821da9e90caad7979373188f9488496800c94746b1955e8aaabdca0fc6d',
		enode: 'enode://be6a094cb5cbef591ac4dc53e82473f29df312e88f804fc110232e8d7972341149bc1bed778893940fb1c523206fbb3682b74f112d615888ec083fe1adca37b5@43.136.53.179:30311'
	},
	{
		owner: 'cijin',
		type: 'witness',
		ip: '106.53.39.89',
		id: '73741045125ed13335ab0440857a745473d43edc5bd5667f92f44e021aa9bf01',
		enode: 'enode://662cbf6b247cd57069c219cdcc23c279af0b0b9679d1161051a999659aef4cf4d5d4f36ee921c60bd52136133d066626f9d7a91e8c2e52f4152d78464ffe9021@106.53.39.89:30311'
	},
	// 20230117 
	{
		owner: '煜歌',
		type: 'witness',
		ip: '43.139.56.55',
		id: 'df0bc83006e72d1bafe079a6116f6724d2af319729affa4995566ae0ae382ded',
		enode: 'enode://e209c2d53cf6756b258f5bde5463c42acfd4c972cf738520e028d8aeefe213c499a45f9aa709bbeb877d4f45cb42c953c7fe09da7a3a4af5bec8e09ccabfa8cf@43.139.56.55:30311'
	},
	{
		owner: '火星',
		type: 'miner',
		ip: '47.100.127.191',
		id: 'eee09cee70c41c21c6ab1ae71236f3e96660d5f7a50b9cc69a276b67d375032f',
		signer: '0x87d973cAD9fE24252F5E4bFbd43B66bF31718886',
		enode: 'enode://1ac2352580896800012fb5461ebafcea10289d07dcf8adaf4d45bb4da57eaf71c650b58030e27d1d0c71096c638b416b70547511e22d6f9716c06236e1785a78@47.100.127.191:30311'
	},
	{
		owner: 'Victor',
		type: 'witness',
		ip: '82.156.203.241',
		id: '72d5165a01039077bd550031acd685b51757dee050ae82c079093d4c6110ae62',
		enode: 'enode://4103ca472d846857ac82c776ce756dad92677375979d8aa88a0c513f3efdfac92c66956170b1c7a35a6b1f7fc9c6d7d69ad4cfe003de7e73d849b0620b1f17e7@82.156.203.241:30311'
	},
	{
		owner: '琰熙',
		type: 'witness',
		ip: '81.70.96.124',
		id: 'ca07c3fd5d80c85ca7666239fc8c7d5390dd603f18d7dca589a1e1b6c4d0c0cb',
		enode: 'enode://59c87271256f37acd8b133e1e94e7b61229265abdd3f85679864fe896d487bf589c29a7deb31252240e87d67acd95fc388ce76b4f5d99be73ada267497ca7d20@81.70.96.124:30311'
	},
	// 24018
	{
		owner: '楼兰渔夫',
		type: 'witness',
		ip: '122.51.121.3',
		id: '48cb7af478e77423f197a7307e837a3f2977760306030e4d65a58053d1e0f97e',
		enode: 'enode://62cf47bd0aebc81e5a39e08084697427c34be62cd1d9bbedb0686d5ce3dcb2f65b7b1d9342477730c57a4e19a7b50eb40fd19f25e6647e5fc4493cc3ce836cca@122.51.121.3:30311'
	},
	{
		owner: '王十二',
		type: 'witness',
		ip: '118.25.110.178',
		id: '37e7770b84e07ea53619accc35646db5bf151af9204e5432770ae718ca9bf0c5',
		enode: 'enode://d05756439dae0a29996a33259616c6476df32d7c99273bb60514028121e9dde0d8ccb9deb4e64ed62f0468227752ac189d23508cf9345fec6aab056237782131@118.25.110.178:30311'
	},
	{
		owner: '明海云',
		type: 'miner',
		ip: '129.204.236.149',
		id: 'cfae8e5f430c68db93d8d85987fa7dc20f17da1bb478f90477ff880f68452024',
		signer: '0xf3b67b1e625a8ffe7af9645e9e1432d145f2046a',
		enode: 'enode://7d2f86c4a16a46aa62674c713c44d9b1c2a0bbcee4e4315c1a9eed47e87c3dfe59916f971bfe5f8b71acd2b5165a89b858569a18a8d12e51bd12273ffc485cbf@129.204.236.149:30311'
	},
	// 240120
	{
		owner: 'kylin',
		type: 'witness',
		ip: '43.139.212.24',
		id: 'bfd47c188a710f4add2d0fb6509b27bddf705e419454846a1d3bd47c10a6ba59',
		enode: 'enode://7a140323b227854dd3fc0929bde47ba3e9c0d3b6156f699eee2a1409e43d3d9e732b0e92eb042b1de9899f519e3d6c176e89423c4e1100ff61f7a62a1c2d1af4@43.139.212.24:30311'
	},
	{
		owner: 'li17.eth',
		type: 'witness',
		ip: '111.229.136.60',
		id: 'b764135d654d36f9566a35d203fe7172a1b452b644d22bee05800a5ccc74cee9',
		enode: 'enode://d56a5ecae9b5afff1d40dba22ee132217267c76f05db004ee8df8629902c9b07ba2f3ce9243407099324137c296e7d287e852ff7d4d92f61820d23203eb631e8@111.229.136.60:30311'
	},

]

// add peers in case if not
const all_ids = admin.peers.reduce((ids, n) => ids.concat(n.id), [])
for (const node of core_nodes) {
	if (!all_ids.includes(node.id))
		admin.addPeer(node.enode)
}

// do stats
var this_node
const id_nodes = {} //nodes indexed by id
const signers = {} //miner nodes indexed by lc(signer address)
for (const node of core_nodes) {
	id_nodes[node.id] = node
	if (node.type == 'miner') {
		signers[node.signer.toLowerCase()] = node
	} else if (node.type == 'witness' && node.id == admin.nodeInfo.id) {
		this_node = node
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

// count live nodes only
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

// the reporting func
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

//print this audit node itself after miners but before witness + miner*
const node = this_node
console.log(node.type + '(a)', node.ip, '✅', 'connected', node.owner, '0')

// second scan, miner* (miner ready candidate - after PoS, before voting)
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'miner*')
		report(node)
}

// third scan, connected witness
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'witness' && node.status)
		report(node)
}

// fourth scan, disconnected witness
for (const [id, node] of Object.entries(id_nodes)) {
	if (node.type == 'witness' && !node.status && node.id != this_node.id)
		report(node)
}
