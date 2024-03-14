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

core_nodes = [
        {
            'owner': 'JNSDAO',
            'type': 'witness',
            'ip': '43.134.121.187', # bootnode.jnsdao.com
            'id': '2379e2c19b8a0e4a76d011b07e41493902c1f274abc5adce3e20fe60f0cabac6',
            'enode': 'enode://19dc6b15744e8ad73f860d6ca7bf7b1acf37497ef8a720a88d64449ec837af460535fcf01662907aaece6bde0c2ff539a9d79e353d043769134666a1586fa4e0@43.134.121.187:30311'
            },
        {
            'owner': 'Jeff',
            'type': 'witness',
            'ip': '43.136.53.164', # bootnode-jeff.jnsdao.com
            'id': '36d1c18a197fea99e9b55b111b03ab03866367838b3017ae91984e0648e3f677',
            'enode': 'enode://f3e4e524d89b4cdb9ee390d9485cee4d6a5e9a260f5673cab118505cc3e69fe8365bc00434222d27fe4082ca798b13ad8e7e139d1315f635fd0e46dbe96fa809@43.136.53.164:30311'
            },
        {
            'owner': 'Koant',
            'type': 'miner',
            'ip': '119.29.202.168',
            'id': '958a680d9c0fd958b21e5f851539c93b12466a668b37dd4eb3b831f28ac1f199',
            'signer': '0xA23e676de107F45A2C873109b6976c1D69b4ad55',
            'enode': 'enode://dbf6ba9d689929e1f8824d53b0e7bd62ceeaff32d65821de5054dd2b48b7701458fb537345c1842c428d5e8918775cffef411e74b073c5d1ff815e78d13270fb@119.29.202.168:30311'
            },
        {
            'owner': '谢勇', #稳清活
            'type': 'miner',
            'ip': '82.157.251.101',
            'id': '6f0ef352cc2536d91f0a55efbec480c8e2b76a11fc5c30830167e026327f0a18',
            'signer': '0x93196aeEb56fe0F5672d84b8F50C123b5dA50329',
            'enode': 'enode://c43fa0ea62dfc0e09906f67a8b730918cbe567a3f53322470780ecdc569efda1a2dd9e4707ac65e3b558e9bf8a025a22da33b1ad08211290211b8c5ed0ed1671@82.157.251.101:30311'
            },
        {
            'owner': 'Jacky',
            'type': 'miner',
            'ip': '47.94.93.119',
            'id': 'e88e333abc2dce665fd9c35bef4a0383249b1670955cefac4c582092fa34fbcb',
            'signer': '0x28D314d2B00EED89041843d4Cd7b9de91170f37a',
            'enode': 'enode://be96ad65107a3d520943f761d00a79a6e08bd4acc5b008b58ff8406761e5ca7e923bcb310654089b1ab364579f70ebe042f2baf9c9adbfa8482052f31c6766f1@47.94.93.119:30311'
            },
        # {
        #     'owner': '一痕',
        #     'type': 'miner',
        #     'ip': '106.75.5.22',
        #     'id': '8118c7cb3f83c1192ed5cdabf3c23798a982faaf2268c5cb2b956dd6d8ecdc2e',
        #     'signer': '0xf7bB10CeDE7E8A0524526577bB4F14390965Cbfa',
        #     'enode': 'enode://91ccd999fe750e950d722f71279c678cae4abdcadfe18e18e2f785871648d386c3db8d2a39fcad49488f6daea4b5d41d3d7cbbb979c31299e9387e0c9d867a37@106.75.5.22:30311'
        #     },
        {
            'owner': '教链',
            'type': 'miner',
            'ip': '82.157.210.13',
            'id': '61cb546c70e6a470e8ee64c4ff5fbef138d9afe116fb24147636802d6ffac30b',
            'signer': '0x85db5D64BD1a2652A75C4A7e12Eeba2f43c57bC4',
            'enode': 'enode://d667d09c38706d40fa1c15cde8dc28c117087cdf55d41d402d70b0817636c6f65e6a6463e81ab178ad9a896ea93c37b479a01ff19dfe13cd4276ea2c64575c76@81.68.150.141:30311'
            },
    {
            'owner': '比尔盖',
            'type': 'miner',
            'ip': '101.43.165.39',
            'id': '32c90f8ee743e588e421c8d374a5ca02ebcabbdc0e6b5b1b912c83185f4522ca',
            'signer': '0x1323caeca07e7bd2b5bdb4bc13e67029ad56fa2f',
            'enode': 'enode://d33540329429582a6c10c917f66103a8e9ce97da24c34bf14d5fd211a8eb4640c6d5ac1a30a764cebd872e6966c04750912726359534a9d4fba5d78c837f4bf0@101.43.165.39:30311'
            },
    {
            'owner': 'Menger',
            'type': 'miner',
            'ip': '62.234.21.37',
            'id': '16376be08813c07d06cdf5e073916f97846c67ec08f1f9c3be4ac5d894ab4670',
            'signer': '0x3fc084c968e77f264803ef5af09e6d6f05228bea',
            'enode': 'enode://72ced57bb2a447947d7bf6378ee927fb04954eba69063571bec3cd3e3cf8d5e660ffb3e62a2cf073045f949a592b2a2c66a1d5bf700a00f069531239749a8382@62.234.21.37:30311'
            },
    {
            'owner': '严光红',
            'type': 'miner',
            'ip': '106.53.60.230',
            'id': 'f92367cc2a9b02c68d6f024b7630bdfa6060d0ce70fc676696633a59eef3ae39',
            'signer': '0xcce6cc1ba66c6b9af2c7b20d78155c74ed9aad6f',
            'enode': 'enode://94b45bc3705c8abebeda0ee9b31a76188b59c0c69397362e96accd39b15a56668775204d4f2e3e7ddb2b14df0b640b5bb9cd4dcb60c252ef80268f1af815f623@106.53.60.230:30311'
            },
    {
            'owner': 'li17',
            'type': 'miner',
            'ip': '47.100.5.124',
            'id': 'ffd502a7cebcaad58aff75d9dfde768067d3e78baf31870a7f4debf353107581',
            'signer': '0x002ed4ea787fd611f44a8277b5e204aad5c81717',
            'enode': 'enode://b7055440d2792887e10ca12192d5d30200a4d9352d9de560732589014e26e5b6c587c5ae201441597795f33b2af6afecadb31193bf6f467024e3144ba40f6d2b@47.100.5.124:30311'
            },
    {
            'owner': '严光红',
            'type': 'witness',
            'ip': '1.14.111.74', # bootnode-ygh.jnsdao.com
            'id': '65e0dc09479950368c2edaa0d7f3dd30af33ebd0187b31f0ad5df55535905f01',
            'enode': 'enode://b3eca38a3d18a789a0ca4e0e871c77fbf98fbe82cb8ed577895be8be14599abd07df88fe5fcf5fa11a63843b25bbc69b28da9a68bc0fcf42b01583329d4e0006@1.14.111.74:30311'
            },
    {
            'owner': '岑云',
            'type': 'witness',
            'ip': '101.34.72.97',
            'id': 'f132b1c2c66c08a1021ce59608238a8322318c14083fbc9ef85bd40e8077d5fe',
            'enode': 'enode://5fa7786fd0f896a680708eaacbf4f5f0f506fe24913e03048b2890abc08faa13183b1618abaa99e042caf3ebebba52aa55d0f1686d5c898d21a74a6cbc13127a@101.34.72.97:30311'
            },
    {
            'owner': '比尔盖',
            'type': 'witness',
            'ip': '62.234.5.241', # bootnode-biergai.jnsdao.com
            'id': 'b3af9021f81a99afb7ae6a09448973453ddab57db15a9f7cfb8db94171d3920d',
            'enode': 'enode://1c4979289156cf90ac190bd6a5f6841886c421ff017dd0d842d8e847973d751f9e13c90e880081c3ba8df5bc572969266c25dac98fc60da68ce6857dcf39da23@62.234.5.241:30311'
            },
    {
            'owner': 'Koant',
            'type': 'witness',
            'ip': '111.230.23.83', # bootnode-koant.jnsdao.com
            'id': '9ff3da439fbb25670e95f0063f7cad9409e66f3283c57fcae0a1e1af9d09cf81',
            'enode': 'enode://b8163bedb4b8e3adf27d94bb8349892f9c8fa14602d2e48bd3083790edc76a26b0ac4d61a44c0a27b2ec46adce2a58249e77b9276530f5116028b355429a9b89@111.230.23.83:30311'
            },
    {
            'owner': 'Leo',
            'type': 'witness',
            'ip': '121.40.97.50',
            'id': '27c01da9e04d8de57b363054772e417a55706cae39f1e5c20abdffe0c3dbe6b7',
            'enode': 'enode://aac8963e6ed260be67d83275faed5cbda6880ecec31abc7e223932c12b5b131d81edc4efb7bc977572afefd6cd3dcd3b4903b44689ca57f8a4f80e935106dacd@121.40.97.50:30311'
            },
    {
            'owner': 'OPEN',
            'type': 'witness',
            'ip': '124.222.199.61', # bootnode-open.jnsdao.com
            'id': '7da1b99acd6bedf5de7ae595aa3676e329b35fc3fa87a93ab0312638549de473',
            'enode': 'enode://0a8b5aa7210ada01d9919e4f1a19860a2946f6e54ae2e0fb8c7e1b7e5482546c478260d284255da92d95d579cffd6ce06ec0bf520b7e4e71876a1efa68f7674d@124.222.199.61:30311'
            },
    {
            'owner': '谢勇',
            'type': 'witness',
            'ip': '120.26.11.88', # bootnode-wenqinghuo.jnsdao.com
            'id': 'cc99492e1e2d2f9b125b8e1faae3c8d0d47eeadc63ac3ac7e58b0767bfde2726',
            'enode': 'enode://b7908693bf2268db08c4fa868d8ea88298e9844a5892681eb63cb4a1a4b254356b5936f6a006dcc709212043b8da325ab72beb3cc2c26cc98843dc301914c961@120.26.11.88:30311'
            },
    {
            'owner': '火星',
            'type': 'witness',
            'ip': '101.32.170.145',
            'id': '9bfbcdd542f8f7af28a9b3c50dc5dbd1bff8085311b9b216716a7106880ad6f2',
            'enode': 'enode://5fe23cce534e7a49a0a6f79203fec02e84391ada79cf8fc0dc8ef2901ddc5620beea52dbab009c6ecb2bdc127ae084a252ffbf5c9221f733d096f346d3f25cf9@101.32.170.145:30311'
            },
    {
            'owner': 'Angel',
            'type': 'witness',
            'ip': '115.159.194.193',
            'id': '00be8ffef4f441c87e65315a3809f94c98197c1e9b614c65f9ca0edb9d00ccb6',
            'enode': 'enode://7d757a706f1c662f63134bfd7439efafb62f11328d0904a3b38677bb27e50632bec061c27e7cbda9eebca08b8040ae96bb04b2de14fc3d9bcb979a8e6d476bfc@115.159.194.193:30311'
            },
    #{
    #        'owner': '如行',
    #        'type': 'witness',
    #        'ip': '47.102.145.16',
    #        'id': '813c74e91083e2a26b8df6abfe9e58ae188e97739690be8815c89dd5515a066f'
    #        },
    {
            'owner': '老谢',
            'type': 'witness',
            'ip': '1.14.106.165',
            'id': '8e38af25891db9f7e3c5e430d4b220910685830ea33cd7a23cc0b0086474aa9e',
            'enode': 'enode://8d820aefee882f7767be1035cbe018200c4daf9030482aa5f6b25665b78b6ee31f4e041d9b439e4ea6c0a7cce5cd76b6fffa76f0bb4229ee6751d52947065dfe@1.14.106.165:30311'
            },
    {
            'owner': 'Stars',
            'type': 'witness',
            'ip': '8.210.106.181',
            'id': 'c6d31bf38cd1d1d5c329a08b3a1c3d1d85ed5edd0cfcd9cc5668f1c9ed354342',
            'enode': 'enode://b750ce05ff791ff659481b7ede44338478f4eb816573c9e71aa892df085bab2841c8271c0c534c290c0348d3fd7468ad3df888dd7a286e298ab0d1037295f823@8.210.106.181:30311'
            },
    {
            'owner': '明海云',
            'type': 'witness',
            'ip': '43.139.249.74',
            'id': 'ea8bcbf9ec92291e54472d3390de4c5231b03661609c46087298b5b451543b02',
            'enode': 'enode://256ec7a9357908270c02c39bec8ba1852a71a4892c9fab95de89fe1a78a6839504f2b4ab1c12e877b8f7d3f6646fbc816ff56d707cc56d49de6158e4cc39ba93@43.139.249.74:30311'
            },
    {
            'owner': 'gwendol',
            'type': 'witness',
            'ip': '119.29.222.90',
            'id': 'ef9301f5b766aa299c2b7f1a199447346772dcc5c326529ff257710530aae46e',
            'enode': 'enode://1dc186a0c401bcfc560d7188810ce3290bd7a05a76bc0fc9237a06042576cf1f1c356f8fb556da234950b88c21c08ff2ba70ab4e58564a74ea46a24511ccff7c@119.29.222.90:30311'
            },
    {
            'owner': '狮子猫',
            'type': 'witness',
            'ip': '123.206.109.17',
            'id': 'e97fcd7f8aed3881648f6d2859ed5da1a589ba9e25c43106c5ff51a14e1994e1',
            'enode': 'enode://efc01ff491d277c73394095de99e8d62d25b5b981e03a4de5419d9bbf5bf6dd1ef6b89e169d376970c1a7af4fc73c90fd2d34b954f02c5367e0150911944cc41@123.206.109.17:30311'
            },
    #{
    #        'owner': 'ucanfilm',
    #        'type': 'witness',
    #        'ip': '47.104.106.73',
    #        'id': 'ceceab24a1f11259f9e9b88a1bd40aca659cf9d4426a08bea4a89110cc7e81e4'
    #        },
    {
            'owner': '元码',
            'type': 'witness',
            'ip': '47.95.200.73',
            'id': 'c6b0f385fd54806b3febf12e4aea8906fad1a175773a4790f9965bdfeb674ce4',
            'enode': 'enode://bba7d137900d93f0b2b62ebcb7917055e47c77b34bba2784008b841561b81fa331a84d45f1fa227f49b18500deb9a3b324a18a7761372f8e9ab1f285a590f146@47.95.200.73:30311'
            },
    {
            'owner': 'OPEN',
            'type': 'miner',
            'ip': '43.142.106.3',
            'id': '6cb4e5340a7e5008dfbc3f20f128bc5a6569e343447ecfcd3018304879f28473',
            'signer': '0xa2547655F12DF995E74fC4b9E3192De432b8b56f',
            'enode': 'enode://73cd7670e483a1d7238cf0bdd557236ea554fa343e9bed85e92f2e45cef859f3a1f4a0f7571a18f54090a206fd62132ded8d3327310a2564374cc01ecad65314@43.142.106.3:30311'
            },
    {
            'owner': 'Jeff',
            'type': 'miner',
            'ip': '47.120.35.41',
            'id': '58871675d4f24d7c916b4c3ccad303b3b862abfe125b1650b0177bd8be09e896',
            'signer': '0x0ac52a05a4f87404b03dd58a7ac1427429522222',
            'enode': 'enode://db1d084eaf12722b04600084a9bd5dcdbbff89facedff931629354ac396acf3564082fbae5a933f1bf4332a174bf9374941dc1caa1527f32c909589a26796014@47.120.35.41:30311'
            },
    {
            'owner': 'bonny',
            'type': 'witness',
            'ip': '123.207.42.3',
            'id': '846e5a80a3ffa352be827443689bcae87fa01d47fd00edaab2b103c0d0b5a80d',
            'enode': 'enode://3732ea7ef0e0d52f83e67136a09bfc82dbcdc53ec5fab8fb3d540f55e6a966fa76908fcd06103a0fa31fe140d2fd52ca1782e5e8c0ea8b59d8bae5d650e3f93d@123.207.42.3:30311'
            },
    # {
    #         'owner': 'Mr.',
    #         'type': 'witness',
    #         'ip': '43.136.53.179',
    #         'id': 'f7f5b821da9e90caad7979373188f9488496800c94746b1955e8aaabdca0fc6d',
    #         'enode': 'enode://be6a094cb5cbef591ac4dc53e82473f29df312e88f804fc110232e8d7972341149bc1bed778893940fb1c523206fbb3682b74f112d615888ec083fe1adca37b5@43.136.53.179:30311'
    #         },
    {
            'owner': 'cijin',
            'type': 'witness',
            'ip': '106.53.39.89',
            'id': '73741045125ed13335ab0440857a745473d43edc5bd5667f92f44e021aa9bf01',
            'enode': 'enode://662cbf6b247cd57069c219cdcc23c279af0b0b9679d1161051a999659aef4cf4d5d4f36ee921c60bd52136133d066626f9d7a91e8c2e52f4152d78464ffe9021@106.53.39.89:30311'
            },
    # 20230117 
    {
            'owner': '煜歌',
            'type': 'witness',
            'ip': '43.139.56.55',
            'id': 'df0bc83006e72d1bafe079a6116f6724d2af319729affa4995566ae0ae382ded',
            'enode': 'enode://e209c2d53cf6756b258f5bde5463c42acfd4c972cf738520e028d8aeefe213c499a45f9aa709bbeb877d4f45cb42c953c7fe09da7a3a4af5bec8e09ccabfa8cf@43.139.56.55:30311'
            },
    {
            'owner': '火星',
            'type': 'miner',
            'ip': '122.51.70.192',
            'id': 'eee09cee70c41c21c6ab1ae71236f3e96660d5f7a50b9cc69a276b67d375032f',
            'signer': '0x87d973cAD9fE24252F5E4bFbd43B66bF31718886',
            'enode': 'enode://1ac2352580896800012fb5461ebafcea10289d07dcf8adaf4d45bb4da57eaf71c650b58030e27d1d0c71096c638b416b70547511e22d6f9716c06236e1785a78@47.100.127.191:30311'
            },
    {
            'owner': 'Victor',
            'type': 'witness',
            'ip': '82.156.203.241',
            'id': '72d5165a01039077bd550031acd685b51757dee050ae82c079093d4c6110ae62',
            'enode': 'enode://4103ca472d846857ac82c776ce756dad92677375979d8aa88a0c513f3efdfac92c66956170b1c7a35a6b1f7fc9c6d7d69ad4cfe003de7e73d849b0620b1f17e7@82.156.203.241:30311'
            },
    {
            'owner': '琰熙',
            'type': 'witness',
            'ip': '81.70.96.124',
            'id': 'ca07c3fd5d80c85ca7666239fc8c7d5390dd603f18d7dca589a1e1b6c4d0c0cb',
            'enode': 'enode://59c87271256f37acd8b133e1e94e7b61229265abdd3f85679864fe896d487bf589c29a7deb31252240e87d67acd95fc388ce76b4f5d99be73ada267497ca7d20@81.70.96.124:30311'
            },
    # 24018
    {
            'owner': '楼兰渔夫',
            'type': 'witness',
            'ip': '122.51.121.3',
            'id': '48cb7af478e77423f197a7307e837a3f2977760306030e4d65a58053d1e0f97e',
            'enode': 'enode://62cf47bd0aebc81e5a39e08084697427c34be62cd1d9bbedb0686d5ce3dcb2f65b7b1d9342477730c57a4e19a7b50eb40fd19f25e6647e5fc4493cc3ce836cca@122.51.121.3:30311'
            },
    {
            'owner': '王十二',
            'type': 'witness',
            'ip': '118.25.110.178',
            'id': '37e7770b84e07ea53619accc35646db5bf151af9204e5432770ae718ca9bf0c5',
            'enode': 'enode://d05756439dae0a29996a33259616c6476df32d7c99273bb60514028121e9dde0d8ccb9deb4e64ed62f0468227752ac189d23508cf9345fec6aab056237782131@118.25.110.178:30311'
            },
    {
            'owner': '明海云',
            'type': 'miner',
            'ip': '129.204.236.149',
            'id': 'cfae8e5f430c68db93d8d85987fa7dc20f17da1bb478f90477ff880f68452024',
            'signer': '0xf3b67b1e625a8ffe7af9645e9e1432d145f2046a',
            'enode': 'enode://7d2f86c4a16a46aa62674c713c44d9b1c2a0bbcee4e4315c1a9eed47e87c3dfe59916f971bfe5f8b71acd2b5165a89b858569a18a8d12e51bd12273ffc485cbf@129.204.236.149:30311'
            },
    # 240120
    {
            'owner': 'kylin',
            'type': 'witness',
            'ip': '43.139.212.24',
            'id': 'bfd47c188a710f4add2d0fb6509b27bddf705e419454846a1d3bd47c10a6ba59',
            'enode': 'enode://7a140323b227854dd3fc0929bde47ba3e9c0d3b6156f699eee2a1409e43d3d9e732b0e92eb042b1de9899f519e3d6c176e89423c4e1100ff61f7a62a1c2d1af4@43.139.212.24:30311'
            },
    {
            'owner': 'li17.eth',
            'type': 'witness',
            'ip': '111.229.136.60',
            'id': 'b764135d654d36f9566a35d203fe7172a1b452b644d22bee05800a5ccc74cee9',
            'enode': 'enode://d56a5ecae9b5afff1d40dba22ee132217267c76f05db004ee8df8629902c9b07ba2f3ce9243407099324137c296e7d287e852ff7d4d92f61820d23203eb631e8@111.229.136.60:30311'
            },

    # 240217
    {
            'owner': '得葱',
            'type': 'witness',
            'ip': '81.68.133.122',
            'id': 'ebd1b822d489eaf5decdd24a996ee8b0454211d32d92714665b5eb8b3441e96e',
            'enode': 'enode://03447b508e2305219f89abd9bfbf4ac73d423dcd777394afae229f39dce51402cae9e985877db710ae55e8a5a739c6774086087595d26f0d15d71201c52c23ff@81.68.133.122:30311'
            },
    {
            'owner': '岑云',
            'type': 'miner*',
            'ip': '129.211.15.80',
            'id': '4a9f87d20e8d2095204c8b440f71d7786c46a7ffd490fe4ddb6eb1b31f274397',
            'enode': 'enode://1d3d78ef5dfbc90930d7b74ba743f7e998524b2c9b8ca119699d64eOb66dd7b8b39255d6293ee1a73079849dd64a98ef8780895a9acd4870caa512ca105774ca@129.211.15.8030311'
            },
    {
            'owner': '布道外部山',
            'type': 'witness',
            'ip': '122.51.173.77',
            'id': '46ee255a1be96130da9f775b33cfbfcd7e5095d8a17eb7cac8e7c4c622072dc1',
            'enode': 'enode://b23f9b6c5f6176e5a103630aa8cc4d17b8b15d93a3a611582e265938fd137eaa4eb401576ac14c1aa39288f8a1e8ede03c7c2bf8fc25e41568d0c4a2870b6a3c@122.51.173.77:30311'
            },

# 240303
    {
            'owner': '剪云为裳',
            'type': 'witness',
            'ip': '1.14.204.34',
            'id': '7493b5e591c0be0d64119f34932cef700bf32a7c2b99fcea1e76320b8ffa611e',
            'enode': 'enode://9507b31e074acc737fbc56b4b80551a793c638f93229949ca999c36e0ac19c7e1e19ab7b5c17c8e018df5c1810ebdaf371ba01a8955001ced0f7dcf6b8931cc5@1.14.204.34:30311'
            },

# 240307
    {
            'owner': '剪云为裳',
            'type': 'witness',
            'ip': '49.232.139.194',
            'id': '7335f6c346cc49185722d70a427174b4e799a72d6698a8b99a1f4f518a6b45d5',
            'enode': 'enode://6e0ab00789fc3580e2229d31a831d778a1d32a9066cdef2950bb5867a2dc3efcef26247a870297334f37ccce0bd2c38f1129c6cbcbb3cbe8ac369d8b12a9f64a@49.232.139.194:30311'
            },
# 240313
    {
            'owner': '花开的声音',
            'type': 'witness',
            'ip': '49.232.139.194',
            'id': '7335f6c346cc49185722d70a427174b4e799a72d6698a8b99a1f4f518a6b45d5',
            'enode': 'enode://6e0ab00789fc3580e2229d31a831d778a1d32a9066cdef2950bb5867a2dc3efcef26247a870297334f37ccce0bd2c38f1129c6cbcbb3cbe8ac369d8b12a9f64a@49.232.139.194:30311'
            },
    {
            'owner': '见证节点',
            'type': 'witness',
            'ip': '101.42.40.244',
            'id': '52317d959b7f78fab18d33b828a6ce597e9148a7f7514135ff50dce110c88fa5',
            'enode': 'enode://6240ce58be19e058cd5c7c8f65db50bfb3843ad1535547b6d09c3833713b357cc0fd93a37c7a0a6ef236d0314a7f79c33b21ec1c5e20df72ce592d65f061428a@101.42.40.244:30311'
            },
    {
            'owner': '米高',
            'type': 'witness',
            'ip': '175.24.131.36',
            'id': 'e0c368e2a656cd268eb9dfa555bad9dc9efe58e428bdb753542804853ba161b4',
            'enode': 'enode://0fa0d319592ee2cb959a32a583433685140aba53c3ff0ffe9b6567eab8c96797e566d7cae5a756ccc310b26fa6bf00c86e92d938fc8d27926a89417a42beea26@175.24.131.36:30311'
            },
    {
            'owner': 'Ted',
            'type': 'miner*',
            'ip': '49.7.215.113',
            'signer': '',
            'id': '14980d894f82bcb4552dff587e988c5acc40d9c24f253671d1aaa0debc49540d',
            'enode': 'enode://21bb97b3560aea63b05811283211008332c59feb165beb15af77b451ab6845f3a6fc394d771aaeb400edad8ae17126dc81eb3db9449733c33b74e5443d2ae04f@49.7.215.113:30311'
            },



]

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
        node['block_rate'] = all_miners[node['signer'].lower()]['block_rate']
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
        node_activity = 0

    print(node['type'], node['ip'], node['owner'], enode_connected, node['status'], node_activity, node_liveness)

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

