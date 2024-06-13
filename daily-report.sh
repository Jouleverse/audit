sudo python3 /home/lighthouse/data/audit_network.py /home/lighthouse/data/mainnet/geth.ipc | tee /home/lighthouse/network-status/daily-report.txt | mail -a "Content-Type: text/plain; charset=UTF-8" -s 'jouleverse network audit report - '`date +\%Y\%m\%d` evan@blockcoach.com,gjw00001@126.com,15916208774@163.com,ygh200@126.com,liuyihen@yeah.net,18210085831@163.com,1320058132@qq.com,mengaili1988@126.com,lilei855x@163.com,87420811@qq.com,cyber4cn@gmail.com,28021246@qq.com,gwendol@qq.com,421292662@qq.com,btcuni@163.com,1864850@qq.com,bonnyshi@189.cn,hkyeee@126.com,cjverify@163.com,812431358@qq.com,532794421@qq.com,1507117933@qq.com,139527518@qq.com,wangxbok@126.com,xieyong513@126.com,251619366@qq.com,decong2077@foxmail.com,youngww@126.com,yun.ceny@hotmail.com,527628414@qq.com,3265354002@qq.com,ccie123@139.com,1251534576@qq.com,2324203938@qq.com,zhuhongyi55@126.com,2064404262@qq.com,879935749@qq.com,btcuni@163.com,lna02601@gmail.com,1223932404@qq.com,bluyee@163.com,lingxs@139.com,1033430781@qq.com

cd /home/lighthouse/network-status/

sed -ri 's/\.[0-9]+\.[0-9]+\./.*.*./g' daily-report.txt

cat daily-report.txt

git pull

git add .

git commit -m "update daily report"

git push

echo "OK"