# 三国志英杰传编辑器

## 启动后端

```
python3 backend/reko3data.py
```
默认监听localhost:8888

## 启动前端(react)

```
yarn start
```
默认监听localhost:8000

## 启动前端(jQuery)

无须命令，打开`http://localhost:8888`端口默认进入reko3ed.html前端页面

## 使用方式

* react因为太慢，只能看看序章，不知道怎么保存
* jQuery虽然界面比较辣鸡，但还是可以用的，只是有点不太直观
  * 不能直接加段落
  * 需要加指令时，先手动添加一段指定长度的指令在前一指令后面，再重新读取出来修改
  * 比如`1a 2b 3c`后面需要添加一个`4d 5e`指令，则先将指令修改为`1a 2b 3c 4d 5e`，重新读取将得到两条指令，再重新修改

## 其他问题

* LS11解析程序在backend/ls11
* 所需修改的文件放在backend/reko3下面，已用LS11解压
* react加载组件太慢，序章就花了一分多钟，其他的更可怕
* 后端部分功能解析未完成

## 一些参考资料

* 分析结果
  * http://xycq.online/forum/viewthread.php?tid=23414&authoruid=3497

* 贼兵必反击补丁
  * http://xycq.online/forum/viewthread.php?tid=21934&authoruid=3497

* LS格式压缩文件解析
  * http://xycq.online/forum/viewthread.php?tid=34612&authoruid=25461

* 剧本初步解析
  * http://xycq.online/forum/viewthread.php?tid=239493&authoruid=3497

* rekoed
  * http://xycq.online/forum/viewthread.php?tid=244170&authoruid=3497

