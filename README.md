# GAVDENER

自用影片整理工具.

## features

- [x] 文件整理;
  - [x] 在线查询影片信息(仅支持javbus)
  - [x] 影片类型支持普通番号(`字母-数字`),FC2系列(`FC2-XXXXXX`),一本道/加勒比系列(`XXXXXXX-XXX`)
  - [x] 整理规则
    - [x] 将文件移动至`<target_dir>/<演员名称>/<番号名称>`
    - [x] 无法获取足够信息的文件,不做处理
- [x] 配置文件

## 配置说明

```yaml
general:
  media_dir: 'F:\Watch\AD' # 源文件夹
  target_dir: 'F:\Watch\Porn' # 目标文件夹
  debug: false # 调试模式,若设为true,则不会真正的移动文件.

spider:
  resource_sites: # 资源站顺序(目前只支持javbus,墙内访问需挂梯)
    - 'javbus'
  proxy: # 代理配置, 如无需代理请删除
    http: 'http://127.0.0.1:10809'
    https: 'http://127.0.0.1:10809'
  timeout: 10
  retry: 3

scrapper:
  target_exts: # 文件类型,仅列出的文件类型会被处理.
    - '.mp4'
    - '.avi'
    - '.rmvb'
    - '.wmv'
    - '.mov'
    - '.mkv'
    - '.flv'
    - '.ts'
    - '.webm'
```

