# 创建服务
cp shadowrocket.service /etc/systemd/system/

# 重新加载 systemd 配置
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

# 设置开机自启动
sudo systemctl enable shadowrocket.service

# 启动服务
sudo systemctl start shadowrocket.service

# 查看运行状态
sudo systemctl status shadowrocket.service

# 查看日志输出
tail -f /var/log/shadowrocket.log

# ios端shadowrocket操作
# 上传配置：shadowrocket-配置-长按要上传的配置-导出配置-使用创建的快捷方式上传shadowrocket配置到服务器
# 上传url http://your_ip:8000/upload
# 下载配置：shadowrocket-配置-右上角加号，下载url http://your_ip:8000/download
# 更新已有配置：只会更新conf中[Proxy Group]到[Rule]和[Rule]到[Host]这两段之间的非注释内容，替换为github上clash.ini配置的策略和规则，不会修改其他shadowrocket conf中自己设定的配置。
# 在conf中[General]下的update-url设置为自己的下载url，在配置上长按更新就可以了 
