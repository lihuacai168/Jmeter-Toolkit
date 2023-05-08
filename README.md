最近找工作（已经离职状态）:sob:   
看广深的测开机会  
个人简介：
- 普通全日制本科，8年经验，在虾皮，TCL，广州致景等工作过
- 擅长：Python，Vue，MySQL，Docker，Linux Shell
- 略懂：Go，Kafka，Redis，MQTT，大数据相关
- 弱项：Java，移动端（有ChatGPT Plus加持，我想这不是什么问题）

各位大佬招人或者内推，扫描二维码，带走我  
<img src="https://img.huacai.one/image-20230412095031719.webp" alt="image-20230412095031719" style="zoom:10%;" />

# Jmeter-Toolkit
Jmeter-Toolkit 是一个专门为 JMeter 测试管理而设计的强大工具集。  
通过使用 FastAPI 和 Docker 构建，为用户提供了一个简洁、高效且可扩展的解决方案。  
Jmeter-Toolkit 支持 JMX 文件的上传、执行、查看JMX、查看JTL以及HTML报告生成。  

- [x] **jmx文件上传**
- [x] **jmx文件执行**
- [x] **jmx文件查看**
- [x] **jtl文件查看**
- [x] **html报告生成**
- [x] **合并jmx上传执行查看报告**
- [ ] **jtl文件上传**
- [ ] **jmx文件下载**
- [ ] **jtl文件下载**
- [ ] **jmx文件编辑**
- [ ] **jmx文件参数化**
- [ ] **前端界面化管理**
- [ ] **支持Jmeter插件**
- [ ] **分布式执行**
- [ ] **使用数据库管理文件**


# 使用演示
## 1. 上传，执行，报告一条龙
![jmx-upload-execute-report.gif](docs%2Fjmx-upload-execute-report.gif)

## 2. 上传JMX文件并执行
![upload-execute.png](docs%2Fupload-execute.png)
## 3. 查看报告
![report.png](docs%2Freport.png)
# 快速启动
## 1. 安装 Docker
请参考 [Docker 官方文档](https://docs.docker.com/engine/install/) 安装 Docker。

## 2. 安装 Docker Compose
请参考 [Docker Compose 官方文档](https://docs.docker.com/compose/install/) 安装 Docker Compose。  
注意：本项目 Docker Compose 仅支持 1.x 版本。  
如果你的 Docker Compose 版本为 2.x，请参考 [Docker Compose 2.x 官方文档](https://docs.docker.com/compose/cli-command/)。

## 3. 启动 Jmeter-Toolkit
### 3.1 使用docker
```shell
docker run -d -p 18000:8000 --name jmeter-toolkit -v $(pwd)/jmx_files:/app/jmx_files -v $(pwd)/jtl_files:/app/jtl_files rikasai/jmeter-toolkit:latest
```

### 3.2 使用make(docker-compose)
```shell
make
```

### 3.3 构建本地镜像并且启动(docker-compose)
```shell
make up
```


## 4. 访问 Jmeter-Toolkit
http://localhost:18000/docs




# Contributors
<a href="https://github.com/lihuacai168/Jmeter-Toolkit/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=lihuacai168/Jmeter-Toolkit" />
</a>
