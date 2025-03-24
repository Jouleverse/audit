#!/usr/bin/python

# Usage:
# $ python3 audit_network.py ~/data/mainnet/geth.ipc
# You may need to grant the access for ~/data/mainnet/geth.ipc to current user.

# Revision History:
# 2024.1.24 evan.j initial rewrite from the js version. add checks for rpc 8501 and block height of witness nodes.

import argparse
import functools
from datetime import datetime, timedelta
from web3 import Web3
from web3.middleware import geth_poa_middleware

# 核心节点信息
core_nodes = [
        {
            'owner': 'JNSDAO',
            'type': 'witness',
            'ip': '101.32.253.192', # bootnode.jnsdao.com
            'id': '2379e2c19b8a0e4a76d011b07e41493902c1f274abc5adce3e20fe60f0cabac6',
            'enode': 'enode://19dc6b15744e8ad73f860d6ca7bf7b1acf37497ef8a720a88d64449ec837af460535fcf01662907aaece6bde0c2ff539a9d79e353d043769134666a1586fa4e0@43.134.121.187:30311',
            'since': '20230529',
            'coreId': 25, # maintainer JVCore #id. 尚未获得则删去该字段.
            },
        {
            'owner': 'Jeff',
            'type': 'witness',
            'ip': '43.136.53.164', # bootnode-jeff.jnsdao.com
            'id': '36d1c18a197fea99e9b55b111b03ab03866367838b3017ae91984e0648e3f677',
            'enode': 'enode://f3e4e524d89b4cdb9ee390d9485cee4d6a5e9a260f5673cab118505cc3e69fe8365bc00434222d27fe4082ca798b13ad8e7e139d1315f635fd0e46dbe96fa809@43.136.53.164:30311',
            'since': '20240115',
            'coreId': 29,
            },
        {
            'owner': 'Koant',
            'type': 'miner',
            'ip': '119.29.202.168',
            'id': '958a680d9c0fd958b21e5f851539c93b12466a668b37dd4eb3b831f28ac1f199',
            'signer': '0xA23e676de107F45A2C873109b6976c1D69b4ad55',
            'enode': 'enode://dbf6ba9d689929e1f8824d53b0e7bd62ceeaff32d65821de5054dd2b48b7701458fb537345c1842c428d5e8918775cffef411e74b073c5d1ff815e78d13270fb@119.29.202.168:30311',
            'since': '20231015',
            'coreId': 0,
            },
        {
            'owner': '谢勇', #稳清活
            'type': 'miner',
            'ip': '82.157.251.101',
            'id': '6f0ef352cc2536d91f0a55efbec480c8e2b76a11fc5c30830167e026327f0a18',
            'signer': '0x93196aeEb56fe0F5672d84b8F50C123b5dA50329',
            'enode': 'enode://c43fa0ea62dfc0e09906f67a8b730918cbe567a3f53322470780ecdc569efda1a2dd9e4707ac65e3b558e9bf8a025a22da33b1ad08211290211b8c5ed0ed1671@82.157.251.101:30311',
            'since': '20240119',
            'coreId': 18,
            },
        {
            'owner': 'Jacky',
            'type': 'miner',
            'ip': '47.94.93.119',
            'id': 'e88e333abc2dce665fd9c35bef4a0383249b1670955cefac4c582092fa34fbcb',
            'signer': '0x28D314d2B00EED89041843d4Cd7b9de91170f37a',
            'enode': 'enode://be96ad65107a3d520943f761d00a79a6e08bd4acc5b008b58ff8406761e5ca7e923bcb310654089b1ab364579f70ebe042f2baf9c9adbfa8482052f31c6766f1@47.94.93.119:30311',
            'since': '20230529',
            'coreId': 9,
            },
        {
            'owner': '教链',
            'type': 'miner',
            'ip': '82.157.210.13',
            'id': '61cb546c70e6a470e8ee64c4ff5fbef138d9afe116fb24147636802d6ffac30b',
            'signer': '0x85db5D64BD1a2652A75C4A7e12Eeba2f43c57bC4',
            'enode': 'enode://d667d09c38706d40fa1c15cde8dc28c117087cdf55d41d402d70b0817636c6f65e6a6463e81ab178ad9a896ea93c37b479a01ff19dfe13cd4276ea2c64575c76@81.68.150.141:30311',
            'since': '20230524',
            'coreId': 25,
            },
    {
            'owner': 'Menger',
            'type': 'miner',
            'ip': '62.234.21.37',
            'id': '16376be08813c07d06cdf5e073916f97846c67ec08f1f9c3be4ac5d894ab4670',
            'signer': '0x3fc084c968e77f264803ef5af09e6d6f05228bea',
            'enode': 'enode://72ced57bb2a447947d7bf6378ee927fb04954eba69063571bec3cd3e3cf8d5e660ffb3e62a2cf073045f949a592b2a2c66a1d5bf700a00f069531239749a8382@62.234.21.37:30311',
            'since': '20231027',
            'coreId': 5,
            },
    {
            'owner': '严光红',
            'type': 'miner',
            'ip': '106.53.60.230',
            'id': 'f92367cc2a9b02c68d6f024b7630bdfa6060d0ce70fc676696633a59eef3ae39',
            'signer': '0xcce6cc1ba66c6b9af2c7b20d78155c74ed9aad6f',
            'enode': 'enode://94b45bc3705c8abebeda0ee9b31a76188b59c0c69397362e96accd39b15a56668775204d4f2e3e7ddb2b14df0b640b5bb9cd4dcb60c252ef80268f1af815f623@106.53.60.230:30311',
            'since': '20240109',
            'coreId': 26,
            },
    {
            'owner': 'li17',
            'type': 'miner',
            'ip': '47.100.5.124',
            'id': 'ffd502a7cebcaad58aff75d9dfde768067d3e78baf31870a7f4debf353107581',
            'signer': '0x002ed4ea787fd611f44a8277b5e204aad5c81717',
            'enode': 'enode://b7055440d2792887e10ca12192d5d30200a4d9352d9de560732589014e26e5b6c587c5ae201441597795f33b2af6afecadb31193bf6f467024e3144ba40f6d2b@47.100.5.124:30311',
            'since': '20240107',
            'coreId': 6,
            },
    {
            'owner': '严光红',
            'type': 'witness',
            'ip': '1.14.111.74', # bootnode-ygh.jnsdao.com
            'id': '65e0dc09479950368c2edaa0d7f3dd30af33ebd0187b31f0ad5df55535905f01',
            'enode': 'enode://b3eca38a3d18a789a0ca4e0e871c77fbf98fbe82cb8ed577895be8be14599abd07df88fe5fcf5fa11a63843b25bbc69b28da9a68bc0fcf42b01583329d4e0006@1.14.111.74:30311',
            'since': '20231014',
            'coreId': 26,
            },
    {
            'owner': '比尔盖',
            'type': 'witness',
            'ip': '62.234.5.241', # bootnode-biergai.jnsdao.com
            'id': 'b3af9021f81a99afb7ae6a09448973453ddab57db15a9f7cfb8db94171d3920d',
            'enode': 'enode://1c4979289156cf90ac190bd6a5f6841886c421ff017dd0d842d8e847973d751f9e13c90e880081c3ba8df5bc572969266c25dac98fc60da68ce6857dcf39da23@62.234.5.241:30311',
            'since': '20230802',
            'coreId': 21,
            },
    {
            'owner': 'Koant',
            'type': 'witness',
            'ip': '111.230.23.83', # bootnode-koant.jnsdao.com
            'id': '9ff3da439fbb25670e95f0063f7cad9409e66f3283c57fcae0a1e1af9d09cf81',
            'enode': 'enode://b8163bedb4b8e3adf27d94bb8349892f9c8fa14602d2e48bd3083790edc76a26b0ac4d61a44c0a27b2ec46adce2a58249e77b9276530f5116028b355429a9b89@111.230.23.83:30311',
            'since': '20240220',
            'coreId': 0,
            },
    {
            'owner': 'OPEN', # last update 240331
            'type': 'witness',
            'ip': '43.139.93.218', # bootnode-open.jnsdao.com
            'id': 'fc1b07c32f0254e83cc1983555921c8afc660b913361306d8e91a5e25fbc8549',
            'enode': 'enode://63715006efec64b76a909bb62c33f7afac17187305c66832bc3fcc4ba4dbd4c897e5aab283844f29fa8be1a8f952080715d8fbd6314282880f9f08f9fc26eede@43.139.93.218:30311',
            'since': '20230529',
            'coreId': 16,
            },
    {
            'owner': '谢勇',
            'type': 'witness',
            'ip': '120.26.11.88', # bootnode-wenqinghuo.jnsdao.com
            'id': 'cc99492e1e2d2f9b125b8e1faae3c8d0d47eeadc63ac3ac7e58b0767bfde2726',
            'enode': 'enode://b7908693bf2268db08c4fa868d8ea88298e9844a5892681eb63cb4a1a4b254356b5936f6a006dcc709212043b8da325ab72beb3cc2c26cc98843dc301914c961@120.26.11.88:30311',
            'since': '20240119',
            'coreId': 18,
            },
    {
            'owner': '火星',
            'type': 'witness',
            'ip': '118.89.117.135',
            'id': '9bfbcdd542f8f7af28a9b3c50dc5dbd1bff8085311b9b216716a7106880ad6f2',
            'enode': 'enode://5fe23cce534e7a49a0a6f79203fec02e84391ada79cf8fc0dc8ef2901ddc5620beea52dbab009c6ecb2bdc127ae084a252ffbf5c9221f733d096f346d3f25cf9@101.32.170.145:30311',
            'since': '20230524',
            'coreId': 17,
            },
    {
            'owner': 'Angel',
            'type': 'witness',
            'ip': '115.159.194.193',
            'id': '63b1871768dfd614523b1e4b089be18dba22aaf5ac1ef2c020e7a40fd692eb46',
            'enode': 'enode://65805489a30f566c4afe5a5771b0f7815f269c2f7dcc1ec4cbacf02ee8386d68d150024b79ac75ae2305b141cf5097d05269fb6612e6989c312037ee38be0d47@115.159.194.193:30311',
            'since': '20231025',
            'coreId': 19,
            },
    {
            'owner': '老谢',
            'type': 'witness',
            'ip': '1.14.106.165',
            'id': '8e38af25891db9f7e3c5e430d4b220910685830ea33cd7a23cc0b0086474aa9e',
            'enode': 'enode://8d820aefee882f7767be1035cbe018200c4daf9030482aa5f6b25665b78b6ee31f4e041d9b439e4ea6c0a7cce5cd76b6fffa76f0bb4229ee6751d52947065dfe@1.14.106.165:30311',
            'since': '20240110',
            'coreId': 28,
            },
    {
            'owner': '明海云',
            'type': 'witness',
            'ip': '43.139.249.74',
            'id': 'ea8bcbf9ec92291e54472d3390de4c5231b03661609c46087298b5b451543b02',
            'enode': 'enode://256ec7a9357908270c02c39bec8ba1852a71a4892c9fab95de89fe1a78a6839504f2b4ab1c12e877b8f7d3f6646fbc816ff56d707cc56d49de6158e4cc39ba93@43.139.249.74:30311',
            'since': '20240111',
            'coreId': 7,
            },
    {
            'owner': 'gwendol',
            'type': 'witness',
            'ip': '119.29.222.90',
            'id': 'ef9301f5b766aa299c2b7f1a199447346772dcc5c326529ff257710530aae46e',
            'enode': 'enode://1dc186a0c401bcfc560d7188810ce3290bd7a05a76bc0fc9237a06042576cf1f1c356f8fb556da234950b88c21c08ff2ba70ab4e58564a74ea46a24511ccff7c@119.29.222.90:30311',
            'since': '20240112',
            'coreId': 24,
            },
    {
            'owner': '狮子猫',
            'type': 'witness',
            'ip': '123.206.109.17',
            'id': 'e97fcd7f8aed3881648f6d2859ed5da1a589ba9e25c43106c5ff51a14e1994e1',
            'enode': 'enode://efc01ff491d277c73394095de99e8d62d25b5b981e03a4de5419d9bbf5bf6dd1ef6b89e169d376970c1a7af4fc73c90fd2d34b954f02c5367e0150911944cc41@123.206.109.17:30311',
            'since': '20240112',
            'coreId': 27,
            },
    {
            'owner': '元码',
            'type': 'witness',
            'ip': '47.95.200.73',
            'id': 'c6b0f385fd54806b3febf12e4aea8906fad1a175773a4790f9965bdfeb674ce4',
            'enode': 'enode://bba7d137900d93f0b2b62ebcb7917055e47c77b34bba2784008b841561b81fa331a84d45f1fa227f49b18500deb9a3b324a18a7761372f8e9ab1f285a590f146@47.95.200.73:30311',
            'since': '20240110',
            'coreId': 25,
            },
    {
            'owner': 'Jeff',
            'type': 'miner',
            'ip': '47.120.35.41',
            'id': '58871675d4f24d7c916b4c3ccad303b3b862abfe125b1650b0177bd8be09e896',
            'signer': '0x0ac52a05a4f87404b03dd58a7ac1427429522222',
            'enode': 'enode://db1d084eaf12722b04600084a9bd5dcdbbff89facedff931629354ac396acf3564082fbae5a933f1bf4332a174bf9374941dc1caa1527f32c909589a26796014@47.120.35.41:30311',
            'since': '20240113',
            'coreId': 29,
            },
    {
            'owner': 'cijin',
            'type': 'witness',
            'ip': '106.53.39.89',
            'id': '73741045125ed13335ab0440857a745473d43edc5bd5667f92f44e021aa9bf01',
            'enode': 'enode://662cbf6b247cd57069c219cdcc23c279af0b0b9679d1161051a999659aef4cf4d5d4f36ee921c60bd52136133d066626f9d7a91e8c2e52f4152d78464ffe9021@106.53.39.89:30311',
            'since': '20240114',
            'coreId': 34,
            },
    {
            'owner': '火星',
            'type': 'miner',
            'ip': '122.51.70.192',
            'id': 'eee09cee70c41c21c6ab1ae71236f3e96660d5f7a50b9cc69a276b67d375032f',
            'signer': '0x87d973cAD9fE24252F5E4bFbd43B66bF31718886',
            'enode': 'enode://1ac2352580896800012fb5461ebafcea10289d07dcf8adaf4d45bb4da57eaf71c650b58030e27d1d0c71096c638b416b70547511e22d6f9716c06236e1785a78@47.100.127.191:30311',
            'since': '20240219',
            'coreId': 17,
            },
    {
            'owner': '明海云',
            'type': 'miner',
            'ip': '129.204.236.149',
            'id': 'cfae8e5f430c68db93d8d85987fa7dc20f17da1bb478f90477ff880f68452024',
            'signer': '0xf3b67b1e625a8ffe7af9645e9e1432d145f2046a',
            'enode': 'enode://7d2f86c4a16a46aa62674c713c44d9b1c2a0bbcee4e4315c1a9eed47e87c3dfe59916f971bfe5f8b71acd2b5165a89b858569a18a8d12e51bd12273ffc485cbf@129.204.236.149:30311',
            'since': '20240118',
            'coreId': 7,
            },
    # 240120
    {
            'owner': 'kylin',
            'type': 'witness',
            'ip': '43.153.19.11',
            'id': '278adeb4cba45bbdce929d78048b016aef23569a52d0565fabdb20d8dddf08c5',
            'enode': 'enode://a682649ff17be55986dbc9ed2cf54bb66c0fff4f5ef4c81f23adbc41e82f91d7f1590f38616c619b1151692e8373dc764edd40819bcd45cb1416b8e4c0af229e@43.153.19.11:30311',
            'since': '20240120',
            'coreId': 31,
            },
    {
            'owner': 'li17.eth',
            'type': 'witness',
            'ip': '111.229.136.60',
            'id': '94e08ab29e8dfcdb79e93fb9d69bad0ff7179508f76fef3d70cea901e17591d0',
            'enode': 'enode://55b8cbf1e0776d4094e8b06b64b0545ce468290deda8c6830e6c3eeb5e06d3929a19a1f507591e3e6d985ad2f84c56327ffbd7f704ac00b84a2800b3de7277d7@111.229.136.60:30311',
            'since': '20240120',
            'coreId': 6,
            },

    # 20240217
    {
            'owner': '得葱',
            'type': 'witness',
            'ip': '150.158.49.56',
            'id': '9a970791e61f2c8a45010ce83c9dd332cb4a634241cbcd45d5ee8d8cf23baa54',
            'enode': 'enode://10ac2787e47bd7472721bafa5abd96dceb91fda82953a49a55c49db585f73a2092688f6c8651531aa1d11367abf6258bd3160940ca9d572e17db69999f29ae52@150.158.49.56:30311',
            'since': '20240217',
            'coreId': 36,
            },
    {
            'owner': '布道外部山',
            'type': 'witness',
            'ip': '122.51.173.77',
            'id': '46ee255a1be96130da9f775b33cfbfcd7e5095d8a17eb7cac8e7c4c622072dc1',
            'enode': 'enode://b23f9b6c5f6176e5a103630aa8cc4d17b8b15d93a3a611582e265938fd137eaa4eb401576ac14c1aa39288f8a1e8ede03c7c2bf8fc25e41568d0c4a2870b6a3c@122.51.173.77:30311',
            'since': '20240218',
            'coreId': 35,
            },

# 20240303 
    {
            'owner': '剪云为裳',
            'type': 'witness',
            'ip': '1.14.204.34',
            'id': 'd1e1dda268df19797d5de93db15689c73ee921529a4c6c52c8ca56a7f45b2517',
            'enode': 'enode://a43404214d3037a88c0b042328f39a8e79738feb896ed0e09472a80f167132cd037c32642f706471995e7a2ee2d88a9078a41b7b352c01158fdadda691420e1e@1.14.204.34:30311',
            'since': '20240303',
            'coreId': 37,
            },

# 20240307
    {
            'owner': '花开的声音',
            'type': 'witness',
            'ip': '42.192.22.155',
            'id': 'c035d24a2ee04451b482b48aff6bd58a51ee9bdd92854487e224828a4c4dd468',
            'enode': 'enode://187997b8ea894fb9574968d264baf0c5eab64a1104cabcf4e4d65102d7c73895e0501e4af08690a876490939e50eaf86b45370ab18f02d0a6c9e11e104a40075@42.192.22.155:30311',
            'since': '20240307',
            'coreId': 39,
            },
# 240313
    {
            'owner': '杨敦鹏', # lastupdate 240402
            'type': 'witness',
            'ip': '115.159.190.129',
            'id': 'cbeb747a862d38b8dc1a5f67a27a542f0e3bbb4b80ea9fcfa4c4b4e217728f80',
            'enode': 'enode://34513e0eb5f5613c51f2fb8648138f2cef59bd047ae197be8c28a2808718584d284b5ab02e7a430fa7ad9a1374b23048cd91fa9ad616afa5cb2f4da70f6016bc@115.159.190.129:30311',
            'since': '20240313',
            'coreId': 45,
            },
    {
            'owner': '米高', #240314 update
            'type': 'witness',
            'ip': '175.24.131.36',
            'id': '873df9bf006162e49b051a3edfdd9fc1d938609e6ef130687376a90645b0dd14',
            'enode': 'enode://2b508101e03ea070e67dc39bd3662c19d3dcc31c2a7564ffe636408d421ef7dc287b7f23d7b39dd11e584cab162ced987ea056a53a1e79ff15e43033a6c9989a@175.24.131.36:30311',
            'since': '20240313',
            'coreId': 42,
            },

    {
            'owner': 'Ted',
            'type': 'witness',
            'ip': '36.134.89.81',
            'id': '1e416260cd36231d299160e8a8c24014a02eb4ba1494ad43011d6432b02fc7ef',
            'enode': 'enode://64e36ff9563dd1e50adbc4ebea15b564eddc557f80e4ff1f19da417413d905fc95323a1bd807c8b5108d83a9587e5ead044bb2d2e9c818d9ccc7e407b5ca56c8@36.134.89.81:30311',
            'since': '20240313',
            'coreId': 43,
            },

#20240319
{
            'owner': '团子',
            'type': 'witness',
            'ip': '49.235.152.212',
            'id': '6fc886c96d3862531db85eb7ba62461970106c7abe543e9663e9c16ec6f0d26b',
            'enode': 'enode://bf6a39a59f320c74dc59883f144550a3059a6b7cde84d21acb0f87b546503f014d8c893335557c8e18c940d1d3418b4b6b630c50c786ad69b1fa4fd5a638386b@49.235.152.212:30311',
            'since': '20240319',
            'coreId': 44,
            },

{
            'owner': '邱泳渼',
            'type': 'witness',
            'ip': '124.222.52.62',
            'id': 'c5aaafa61992ef49d76c3bd84e493afac61aa082e83d49fb6d4a80834b005a76',
            'enode': 'enode://979dcadb3ce38e9569da7e9d47c9d99869bfbe62a64e6e36f76755aacc044cacf5cdd3fea96d2863414b164271412ff966adc95b037858bf095d66952c2618e8@124.222.52.62:30311',
            'since': '20240319',
            'coreId': 47,
            },

{
            'owner': '阿震',
            'type': 'witness',
            'ip': '106.53.94.136',
            'id': '358934bef6216ec5c9426feb5edf8cea992a7eb9302a6657a247c8ef0359d882',
            'enode': 'enode://b4f4afa12dc5dc8d5af345be95bc2e99e134639f733be72cc4802ecb74dc36a8dc896c9e2f429371a5e714d4d06b11c9121b0ee509f1e811c87f635b43305491@106.53.94.136:30311',
            'since': '20240319',
            },
# 20240402
{
            'owner': '星语欣愿',
            'type': 'witness',
            'ip': '124.223.91.169',
            'id': 'ef5afb2bcf53d9dc6c2c66717a48140e2723c665da7c27998d6d54859574b28d',
            'enode': 'enode://eb100647b61986fc68bf3298ee2e40caefc452986487776fe9976eb5e8a04592aa162f7aede632ddc041f9ce9557e2e2b981e5a24cdade1823affac662df34f2@124.223.91.169:30311',
            'since': '20240402',
            'coreId': 49,
            },

# 20240419 #update 20240102
{
            'owner': 'jay.j',
            'type': 'witness',
            'ip': '118.25.144.251',
            'id': 'f41b2fc240589c7b9e9061a4e86a314cfb8728b8a75fc4c99e88993ac41a2616',
            'enode': 'enode://c324f07f404da4d2e88bd503ca50194f6d9c7da43d8c726fa326310fa683b350536858a2a51a2a3a4e7953248856162250671b4afd4536e1ae4bd7befabe5e9a@118.25.144.251:30311',
            'since': '20240419',
            'coreId': 50,
            },

# 20240429
{
            'owner': 'ucanfilm',
            'type': 'witness',
            'ip': '139.129.20.205',
            'id': '88bfd5ab83bee2a2c25e7a15911cf780cd0ccac86acd928867e784fcdf47df8c',
            'enode': 'enode://fbb54beade25d2c70ea03422e219ea5ec0d322b6b2a3bfe94eba5bc101c5cbfeba090e5f54014ef1ffa56e537c526730ae668b6e7e0b510565eb6ff6307d4e93@139.129.20.205:30311',
            'since': '20240429',
            'coreId': 14,
            },
# 20240509
{
            'owner': '相瑾',
            'type': 'witness',
            'ip': '101.43.23.92',
            'id': 'bda5a83e2f7c70a33d31a998f285d50da8a09448af9805a5e069d8a780407989',
            'enode': 'enode://620113e75c0cf4a645b9bfe938a147211cbbf84b2f36405f69dfaa359e58032519e7eababe033214966a10579517a588d25060e71e6399459a227c8ef2ecda00@101.43.23.92:30311',
            'since': '20240509',
            'coreId': 51,
            },


# 20240622
{
            'owner': '盛美',
            'type': 'witness',
            'ip': '36.212.86.15',
            'id': '68617066980c00985b7fc331487d193e22258badbaeec6bf619d3e7cbc255ae8',
            'enode': 'enode://9fcb694d575cac90db04e4afd4611145b21b01282ce06097bec90e806f3819656bbc4ce3ea9c41b91f62a4a6fc4300758df0e829e38b708563cf43e5a159ba31@36.212.86.15:30311',
            'since': '20240623',
            'coreId': 52,
            },

# 20240719
{
            'owner': '微尘',
            'type': 'witness',
            'ip': '81.70.93.66',
            'id': '81abaac1ce9838730115e271d14da9d0a437475334a1a9efd4e1b4f1e7696f88',
            'enode': 'enode://c4bb52660680595ffb3a1b7dd4db696c74f69bc9fa29fb93ff46e4d69f32fd6fc06b7470605fe0b1d7e19b30f54dc17170df4865fc668f19f8d842ada83f8867@81.70.93.66:30311',
            'since': '20240719',
            'coreId': 53,
            },

# 20240807
{
            'owner': '张恩畅',
            'type': 'witness',
            'ip': '118.89.117.223',
            'id': 'e5eb6b54bcb84281de04d6c4ff2ff813402512b143381204a530c5ad8d48dff1',
            'enode': 'enode://5d19e0757bd2a307cb425a0db5e34964b1fd3ca07797072103d450101513430eb7d82af4b900af59b75a4deea1a5bca40653877dac2799cbfeca8a7243498522@118.89.117.223:30311'
            ,'since': '20240807',
            'coreId': 15,
            },
# 20240825
{
            'owner': '蓝叶子-node',
            'type': 'witness',
            'ip': '1.92.122.1',
            'id': 'bb341e65ad7fdac57853cd6e016207c99eb6ea07c758d8264fccffee63f0654a',
            'enode': 'enode://f08af9f5fa587deee8b1adb8f14f14918d9cd21c592ab1a7975228a611839f6709d8bc4ef4839c582cc169234e599a9236fa53e7984210bbcf3a7fde691dc070@1.92.122.1:30311'
            ,'since': '20240825',
            'coreId': 60,
            },

# 20240831
{
            'owner': 'sing2011',
            'type': 'witness',
            'ip': '101.126.79.130',
            'id': '6b0da4e2b295d5479d6f856be3b2264bb57c443a23b568d76c40aa0f7774ae1e',
            'enode': 'enode://d8cc45697a68aed642a2f4747d0829716d08b83c8384d3a0f9dc1705f0804efb33216afc11cfd4296b306a2ad18be1984366326d1920a584aa62d9d120896d82@101.126.79.130:30311'
            ,'since': '20240831',
            'coreId': 58,
            },

# 20240908
{
            'owner': 'TIGER',
            'type': 'witness',
            'ip': '162.14.111.59',
            'id': '13b01d9329bbae324a581153eee384d148170bdcb5dc0ff43e2b5749224d483e',
            'enode': 'enode://3abea1f6928c8400900c554fceb6a63a79120214e72bfde6a9ff10f60b147a616585f4b433e25cbac8b37a3efbb5eff36b0dc73961c09858ee15790a2732a3a2@162.14.111.59:30311'
            ,'since': '20240908',
            'coreId': 57,
            },
{
            'owner': '潇先生',
            'type': 'witness',
            'ip': '101.126.91.91',
            'id': '5a7147dbbfb3481999095253015cd0bba34aef5d275c8778dcaefc6868fd815b',
            'enode': 'enode://70ee7da8aee656dd87087a90d9b89d5aec786b11d6d08979588640a57defcb9cb1fb0da4c1c536b8adac84e717885d5b34e641768c6d129478e4f3652ef82d19@101.126.91.91:30311'
            ,'since': '20240908',
            'coreId': 59,
            },

# 20240925
{
            'owner': '彩彩',
            'type': 'witness',
            'ip': '101.126.156.22',
            'id': '1519723d38021e865a05454ca2b1c8f42a47ebe79eb5d7f5756608bb17c153f5',
            'enode': 'enode://d391c5ce8898eece6d7aaaf23ebcd7caa342c9bc9406645f9be617fa3e405af07cd80beb56dcabb12317f8b46bb57cf67e8a6f631ddc09f8b9733c5041e74516@101.126.156.22:30311'
            ,'since': '20240925',
            'coreId': 61,
            },


{
            'owner': 'Simon',
            'type': 'witness',
            'ip': '139.224.209.54',
            'id': 'b9ee64eeca1fcedad05629a41665df21e395900de11e8d84f785d773b4ccbcec',
            'enode': 'enode://bfda1116bba6ac01a61479acf917fc45b667d9bed824f21d6e1acfc04e546c8d2ce1b629e2c924797eb43243188586544de5618f6aadc97c70916d31e10b7fff@139.224.209.54:30311',
            'since': '20240927',
            'coreId': 54,
            },

    # 241103
    {
            'owner': 'kylin',
            'type': 'miner',
            'ip': '110.40.130.38',
            'id': '4c1caaabecd77700cbe29f5ffda48370dbddaf9def2ebafdb1471736b27d1e8b',
            'signer': '0x08c1938546708f0b3c6f49703d1c19f79d90ac04',
            'enode': 'enode://2e4104827d8fe8344b10d9ec10705e7cba11ef8476f68d0b5d7ceafe747373f03b2074e5901ba3c5d25c0436a24c03504cb75334e5503a65a1dc6929e0bd2346@110.40.130.38:30311',
            'since': '20241103',
            'coreId': 31,
            },

    # 241113
    {
            'owner': '剪云为裳',
            'type': 'miner',
            'ip': '106.54.199.222',
            'id': '4c108deb46bbe44e5960b509d1afd625cbeba13033fd92759ba8cc59b52d3a2f',
            'signer': '0x5bC3930448cE53C970AcD41C1f80AbA6ab3c523f',
            'enode': 'enode://2f151d76573e56ee0f57f5598176a5efe1a7fa3f154f66f5674257fe565138d0d4e80b3cba9cc12db0322a9bfd9ef1dc48e79f12cad9233d483f6c3d7d5d9b71@106.54.199.222:30311',
            'since': '20241113',
            'coreId': 37,
            },

    # 241115
    {
            'owner': '微尘',
            'type': 'miner',
            'ip': '1.92.102.75',
            'id': '5c488a3f6e2a73da519a6b761164492fd3e9881d5d2537f8ebecbc5718549014',
            'signer': '0xff42f7a9fd1afdeed1568805fa8dce67e3dbc188',
            'enode': 'enode://a1224775395a3d283ac745ab6960b24dd8c432cba108be82331c7eeb8c2a8c361387446e64c4ff99c91e89fd730a0c56a7b29927771291006d02a023eabfa63b@1.92.102.75:30311',
            'since': '20241115',
            'coreId': 53,
            },

    # 241117
    {
            'owner': '煜歌',
            'type': 'miner',
            'ip': '110.42.247.135',
            'id': '40516132d629c367140578751bb341fc774c7b84e9983eb4e605e9f1bf052479',
            'signer': '0xa3F01Afa1dDfB6D07cac35210d5AFdfe6f0982E8',
            'enode': 'enode://4dae7c25cc4f3d379911c3386f2a50f07142a0a8b5ba953d26ffc5ea9b3a8bd8b858ae18ab1b56887708c29b39949e9745fb65c9427de61ae6e20c74593373a2@110.42.247.135:30311',
            'since': '20241117',
            'coreId': 33,
            },

{
            'owner': '富轩',
            'type': 'witness',
            'ip': '110.42.233.253',
            'id': '2180a1ff8fc303c5411e4421a5bbb362424972ff4c367fc7074a165b8a32a29e',
            'enode': 'enode://ff3e0e9c8ea5442ab3d0f2adddf1879aa8a51bd082a6718ac2289a656887c0c1f6e1fc4d08233aa33df4e6e21fef3deb90a1ae8b62bbc46dca392d570942e594@110.42.233.253:30311',
            'since': '20241118',
            },

{
            'owner': '佘小强',
            'type': 'witness',
            'ip': '119.45.93.155',
            'id': '2c3cbf2abba1708a0b55a80ab8498339ebb1c150a89c83504923a5c241426658',
            'enode': 'enode://e44ca285b8f72d3188ca47dffe9a83c84bd92b80dc2e7e1ee30a4474656aa815da87406c939c218be453bb329d792ff44ccd7eb6fc2ab9795bcea159d27b7a3b@119.45.93.155:30311',
            'since': '20241121',
            'coreId': 56,
            },


{
            'owner': '尧垚',
            'type': 'witness',
            'ip': '124.222.176.129',
            'id': 'be70a66bda6583faeb550fd4971ea7bc8479a191006ef8d3669861e7117de12d',
            'enode': 'enode://6a3591331386ba44f0363e47d8f624a70f4ed1d1a54d1788180ca7ef2d0d70104e77a270f3c44ebeddd2b1a5c778b8952d71b972d876b0c947fbf0f683d9ef0f@124.222.176.129:30311',
            'since': '20241124',
            },

{
            'owner': '蓝色经典',
            'type': 'witness',
            'ip': '124.221.46.91',
            'id': 'a2d15ab7082a46867c6ce08b62c2634a4f26fb65958ba6c715e1f2eeac5acae8',
            'enode': 'enode://0c8e3ec717871091769e0a3f9f63ca91dc2d74e3648d6cae9f508127d95c0fd8cbba66c5b551ecd962a02af95171fc6b9fa78cba783c8837e4931a81dd253f9b@124.221.46.91:30311',
            'since': '20250107',
            'coreId': 55,
            },
        {
            'owner': 'cijin', 
            'type': 'miner',
            'ip': '139.155.147.177',
            'id': 'bd872df0367eafd723691769eff10a255840ad16ebaebed534d8340be43358d8',
            'signer': '0x6c1094955e6d5ffd62729f642ee78b8237f82d7c',
            'enode': 'enode://ddacebd479562a78171680fdfe61596d4207c8642eb8bec8c74852b4a859f139676a158cadda8f812c31596b2fa65839637b0d034987fb48c17185fdf50@139.155.147.177:30311',
            'since': '20250311',
            'coreId': 34,
            },
        {
            'owner': '煜歌', 
            'type': 'witness',
            'ip': '42.193.109.237',
            'id': 'c0a15305660cdb54249dc6779625e3004c74cbfa4fd369e7ce549e5b3c13208e',
            'enode': 'enode://2ff621a918f56499f6d7c2a220b9fe5b0db61ca0360b8915f4553bdb0c7f600ff065beb5499da4ac4afaa2861144197f4d01764a679070a71edb6402f3bd6c11@42.193.109.237:30311',
            'since': '20250316',
            'coreId': 33,
            },
        {
            'owner': '楼兰渔夫', 
            'type': 'miner',
            'ip': '110.42.225.146',
            'id': '944ad2cd26b56cd6e5b35d9878f5efc05a713d91d1c584af63529bd1592b67f2',
            'signer': '0x497c19a8157f2c839ec57bf6fb0f26c44fa51203',
            'enode': 'enode://840f6fbc0650bc100daec33dd6707a3ad7672204e849de83a20c3b5b8a3a3705c974f6801e3d26af22b26c9b0194c9fcd804144dc1a4e2da2f6b10b09b707258@110.42.225.146:30311',
            'since': '20250319',
            'coreId': 4,
            },
]

# JVCore 合约 ABI
jvcore_abi = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "isLiveness",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# JVCore 合约地址
jvcore_address = "0x8d214415b9c5F5E4Cf4CbCfb4a5DEd47fb516392"

## parse command line argument /path/to/geth.ipc
parser = argparse.ArgumentParser('audit_network')
parser.add_argument('geth_ipc', help='path to geth.ipc file to be attached to')
args = parser.parse_args()
geth_ipc = args.geth_ipc

## try to attach
w3 = Web3(Web3.IPCProvider(geth_ipc))
if not w3.is_connected():
    raise Exception('cannot attach to geth ipc: ', geth_ipc)

w3.middleware_onion.inject(geth_poa_middleware, layer=0) #otherwise cannot get_block

## 创建 JVCore 合约实例
jvcore_contract = w3.eth.contract(address=jvcore_address, abi=jvcore_abi)

## get id of this node (as audit node)
audit_node_id = w3.geth.admin.node_info().id

## restructure node data
all_peers = w3.geth.admin.peers()
all_connected_ids = functools.reduce(lambda ids, n: ids+[n.id], all_peers, [])

all_nodes = {} #nodes indexed by id
all_miners = {} #miner nodes indexed by lc(signer address)

for node in core_nodes:
    all_nodes[node['id']] = node
    if node['type'] == 'miner':
        all_miners[node['signer'].lower()] = node

    ## add peers in case if not
    if node['id'] == audit_node_id:
        all_nodes[node['id']]['status'] = 'connected'
        all_nodes[node['id']]['type'] = 'witness(a)'
    elif node['id'] in all_connected_ids:
        all_nodes[node['id']]['status'] = 'connected'
    else:
        all_nodes[node['id']]['status'] = 'disconnected'
        print('disconnected. trying to add peer:', node['ip'], node['type'], node['owner'])
        w3.geth.admin.add_peer(node['enode'])

## update all_miners with information from clique.status
clique_status = w3.provider.make_request('clique_status', [])['result']
for (addr, n) in clique_status['sealerActivity'].items():
    if addr.lower() in all_miners:
        all_miners[addr.lower()]['block_rate'] = n / clique_status['numBlocks']

## get latest block info
last_block_n = w3.eth.get_block_number()
last_block = w3.eth.get_block(last_block_n)
last_block_t = datetime.fromtimestamp(last_block.timestamp)
current_t = datetime.now()
diff_t = current_t - last_block_t

## update all nodes status (miners + witness) and count
count = count_miner = count_witness = 0
for (id, node) in all_nodes.items():
    node_type = node['type']
    if node_type == 'miner':
        node['block_rate'] = all_miners[node['signer'].lower()].get('block_rate') or -1 
        if node['block_rate'] > 0:
            count_miner += 1
            count += 1
    elif node_type == 'miner*':
        node['block_rate'] = 0
    elif node_type in ['witness', 'witness(a)']:
        #node['block_height'] = 0
        # check witness node's rpc 8501 and block height
        ww3 = Web3(Web3.HTTPProvider('http://' + node['ip'] + ':8501'))
        if ww3.is_connected():
            node['block_height'] = ww3.eth.get_block_number()
        else:
            node['block_height'] = 0

        diff_blocks = abs(node['block_height'] - last_block_n)
        if diff_blocks < 10:
            count_witness += 1
            count += 1

## output report
print('Jouleverese Network Audit Report')
print('===============================================')
print('Report Time:', datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z"))
print('------------- blockchain status ---------------')

if diff_t < timedelta(seconds=60):
	print('Blockchain Status: 🟢')
else:
	print('Blockchain Status: 🔴')

print('Latest Block Height:', last_block_n)
print('Latest Block Time:', last_block_t.astimezone())

## reporting node counts
print('Network Size: ', count, ' nodes (', count_miner, ' miners, ', count_witness, ' witnesses, miner*s excluded)')

## reporting node status
print('---------------- nodes status -----------------')
print('TYPE', 'SINCE', 'IP', 'OWNER', 'CHECK-IN', 'CORE-ID', 'CONNECTED', 'STATUS', 'ACTIVITY', 'LIVENESS')
print('-----------------------------------------------')
## helper: reporting func
def report(node):
    enode_connected = '🟩' if node['status'] == 'connected' else '🟥'
    if node['type'] == 'miner' and node['block_rate'] > 0:
        node_liveness = '✅'
        node_activity = node['block_rate']
    elif node['type'] in ['witness', 'witness(a)'] and node['block_height'] > 0:
        node_liveness = '✅'
        node_activity = node['block_height']
    else:
        node_liveness = '❌'
        node_activity = -1

    # 获取节点的 check-in 状态
    core_id = node.get('coreId')  # 获取 coreId，可能为 None
    if core_id is not None:
        check_in_status = jvcore_contract.functions.isLiveness(core_id).call()
        check_in_status_display = '👍' if check_in_status else '💔'
    else:
        core_id = '--'
        check_in_status_display = '❔'  # 缺失 coreId，显示为未知状态

    print(node['type'], node['since'], node['ip'], node['owner'], check_in_status_display, core_id, enode_connected, node['status'], node_activity, node_liveness)

## reporting miner status first
for (id, node) in all_nodes.items():
    if node['type'] == 'miner':
        report(node)

## reporting this audit node
report(all_nodes[audit_node_id])

## reporting miner*
for (id, node) in all_nodes.items():
    if node['type'] == 'miner*':
        report(node)

## reporting witness alive
for (id, node) in all_nodes.items():
    if node['type'] == 'witness' and node['block_height'] > 0:
        report(node)

## reporting witness suspicious to not alive anymore
for (id, node) in all_nodes.items():
    if node['type'] == 'witness' and node['block_height'] == 0:
        report(node)
