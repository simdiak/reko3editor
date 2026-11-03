# 三国志英杰传编辑器

《三国志英杰传》（Reko3，繁体 Big5 版）的剧本/对话修改器。后端用 Python(Flask) 解开游戏自身的 LS11 压缩数据，把每章的剧情文本(SNRM)和剧本指令(SNRD)翻译成中文对照显示，改完后重新打包下载，另外还能查看人物等基础数据。

## 目录结构

```
reko3editor/
├── backend/
│   ├── api.py              Flask 服务，提供全部 HTTP 接口（历史入口名为 reko3data.py）
│   ├── libs/__init__.py    核心：Reko3Data 类，解析/回写全部游戏数据
│   ├── libs/data_maps.py   静态数据表：军、触发类型、指令长度与说明、建筑、AI
│   ├── libs/common.py      小端读取、hex 格式化等工具
│   ├── reko3ed.html        jQuery + JSONEditor 单文件前端（目前真正可用的前端）
│   ├── static/             jquery / bootstrap / jsoneditor
│   ├── reko3/              已 LS11 解压、可直接编辑的数据文件
│   ├── reko3.orig/         原始数据备份（sync.sh 用于还原与部署）
│   └── sync.sh             部署脚本（scp 到服务器）
├── src/                    React 版编辑器（未完成，见下文）
├── utils/ls11/ls11.cpp     LS11 解压算法的 C++ 实现
└── utils/reko3.tar.bz2     原始数据打包
```

## 启动后端

```
cd backend
export DEBUG=True        # 不设置则监听16661端口，且不开启debug
python3 api.py
```

* 依赖 flask（`pip install flask`）；`reko3_dir = "./reko3"` 是相对路径，必须在 `backend` 目录下启动
* 设置 `DEBUG=True` 时监听 `0.0.0.0:8888`（debug 模式），否则监听 `0.0.0.0:16661`
* 打开`http://localhost:8888`默认进入reko3ed.html前端页面
* 线上部署时通过反向代理挂在 `/reko3edit` 路径下（页面内所有请求都带该前缀），本地直连需要自行加前缀映射

## 启动前端(react)

```
yarn start
```
默认监听localhost:8000

* `src/Settings.js` 里的 `base_url` 需改成后端实际地址（当前硬编码为 `http://10.212.19.229:8888`）
* 目前只加载了第 0 章，加载极慢且没有保存功能，仅作参考

## 启动前端(jQuery)

无须命令，打开`http://localhost:8888`端口默认进入reko3ed.html前端页面（端口取决于后端的 DEBUG 设置）

## 使用方式

* react因为太慢，只能看看序章，不知道怎么保存
* jQuery虽然界面比较辣鸡，但还是可以用的，只是有点不太直观
  * 不能直接加段落
  * 需要加指令时，先手动添加一段指定长度的指令在前一指令后面，再重新读取出来修改
  * 比如`1a 2b 3c`后面需要添加一个`4d 5e`指令，则先将指令修改为`1a 2b 3c 4d 5e`，重新读取将得到两条指令，再重新修改

## 数据文件

`backend/reko3/` 下是已解压的游戏数据：

| 文件 | 内容 |
| --- | --- |
| `Snr0d.r3` ~ `Snr4d.r3` | 各章剧本指令（SNRD），LS11 压缩 |
| `Snr0m.r3` ~ `Snr4m.r3` | 各章剧情文本（SNRM），Big5 编码 |
| `Bakdata.r3` | 384 名武将的基础属性、初始属性、初始道具表 |
| `Main.exe` | 兵种名、策略名表（按硬编码偏移读取） |

## 解析原理

SNRD 被解析成四层结构：

* page（章/子章，索引中压缩大小为 0 表示结束）
* paragraph（段，以 `0xffff` 结束）
* section（组指令，10 字节表头＝类型＋子段号＋16 位偏移，以 `ff ff` 结束）
* script（段内指令流，按 `data_maps.code_step` 中每个 opcode 的 `plen` 长度切分）

`code_step` 把 opcode 映射成中文说明（如 `0x03 部署我军部队`、`0x1C 改变人物AI`、`0x22 部署敌军`），`resolv_script_instr()` / `get_trigger_info()` 再把参数翻译成人话，例如：

```
2e 01 00 00 00 ff  切换所在城市 城市=1
09 00 20           指定战场/场景/大地图 进入 城市-宫殿
0a 7e 01 19 06 02  部署非战斗模式中的人物 [獻帝] (25,6) 朝向2
```

SNRM 文本分两类：前两字节为人物 ID（小于 0x180）的是「带头像对话」，其余为「一般文本」，均按 Big5 解码。保存时 `write_snrd()` / `write_snrm()` 会重建 LS11 头部与 page/paragraph/section 的索引偏移，所以修改文本长度后地址会自动重算。

LS11 格式大致为：0x10 字节头 + 0x100 字节字典 + 段索引（压缩大小/原始大小/偏移）+ 位流 LZ 压缩数据，解压实现见 `utils/ls11/ls11.cpp`。

## 后端接口

| 接口 | 说明 |
| --- | --- |
| `GET /` | 返回 reko3ed.html |
| `GET /load_snrm/<n>`、`GET /load_snrd/<n>` | 读取第 n 章的文本/指令（已裁剪为前端所需字段） |
| `POST /write_snr/<n>` | 回写第 n 章，自动重算索引偏移 |
| `POST /upload_snr` | 上传本地 snrd/snrm 到 /tmp 进行编辑 |
| `GET /download_snr/<t>/<n>` | 下载生成的第 n 章（t 为 d/m） |
| `GET /trans/<data>` | 中文转 Big5 字节码，遇非 Big5 字符会返回出错的字 |
| `GET /load_avatar`、`/load_avatar_first`、`/load_bingzhong`、`/load_daoju`、`/load_ai`、`/load_juntuan`、`/load_trigger`、`/load_script_code`、`/load_instr_index_code` | 各类静态数据表 |
| `GET /load_resource` | 汇总返回前端所需的全部数据表 |

## 已知限制

* 道具 / 兵种 / 策略三个页面只是占位，人物页面只能查看初始数据、不能保存
* 不能直接新增段落，需要加指令时按「使用方式」里的办法先补足长度再重新读取
* React 版加载极慢且无法保存，形同废弃
* 后端仍有部分指令类型未解析（`data_maps.code_step` 中标注为「未知」的项）

## 其他问题

* LS11解析程序在backend/ls11（`Encode` 只留了空壳，未实现压缩）
* 所需修改的文件放在backend/reko3下面，已用LS11解压
* react加载组件太慢，序章就花了一分多钟，其他的更可怕
* 后端部分功能解析未完成

## 一些参考资料

* 分析结果
  * https://xycq.org.cn/forum/viewthread.php?tid=23414&authoruid=3497

* 贼兵必反击补丁
  * https://xycq.org.cn/forum/viewthread.php?tid=21934&authoruid=3497

* LS格式压缩文件解析
  * https://xycq.org.cn/forum/viewthread.php?tid=34612&authoruid=25461

* 剧本初步解析
  * https://xycq.org.cn/forum/viewthread.php?tid=239493&authoruid=3497

* rekoed
  * https://xycq.org.cn/forum/viewthread.php?tid=244170&authoruid=3497

