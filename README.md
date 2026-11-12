# gh-pages

这个分支只放网站文件，由 GitHub Pages 发布。

- `index.html`：Nasdaq-100 分段直线拟合的交互页面，数据和脚本都内嵌在这一个文件里，不依赖外部资源。
  页面是中英双语的，右上角可以切换；网址后加 `#en` 或 `#zh` 可以直接打开对应语言。
- `.nojekyll`：让 GitHub Pages 直接发布静态文件。

数据和抓取脚本在 `main` 分支。

开启方式：仓库 Settings → Pages → Source 选 “Deploy from a branch”，Branch 选 `gh-pages`、目录选 `/ (root)`，保存。
