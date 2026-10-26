# 下载完整归档

本仓库保留原交付文件及哈希清单。超过普通 Git 文件大小上限的数据库快照通过 Git LFS 保存。

已安装 Git LFS 时，使用以下命令获取完整文件：

```bash
git clone https://github.com/ZYDTR/truthinsight-v3-five-conversations-20261017.git
cd truthinsight-v3-five-conversations-20261017
git lfs install --local
git lfs pull
python3 tools/verify_archive.py
```

如果数据库文件只有几行 `version https://git-lfs.github.com/spec/v1` 开头的内容，表示拿到的是 LFS 指针，请运行 `git lfs pull` 下载原文件。GitHub 的源码 ZIP 可能只包含该指针，推荐通过上面的命令克隆。

`MANIFEST.sha256` 对应原始交付包的 6606 个文件；新增的 `.gitattributes` 与本下载说明不在该原始清单内。
