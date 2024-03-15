# Hello ElementAstro Launcher

## 简介

基于 FireflyLauncher 进行二次开发的 GUI 启动器，支持启动各种类型的天文软件。

## 使用

### 安装

#### 方法一(普通)

从本仓库的 [Release](https://github.com/ElementAstro/HEAL/releases) 下载对应操作系统的稳定版本

#### 方法二(进阶)

从本仓库的 [Actions](https://github.com/ElementAstro/HEAL/actions/) 下载对应操作系统的开发版本

#### 方法三(开发)

克隆本仓库，从源码构建 GUI，目前运行 build.bat 可一键构建源码(无虚拟环境)

### 构建

解压文件或者构建，以下是构建完成后的文件目录

![image](https://github.com/ElementAstro/HEAL/assets/77842352/2118e3a4-afa0-4683-9a1a-ca11084851a7)

### 字体

下载字体文件并安装，[字体文件](https://github.com/ElementAstro/HEAL/releases/download/v1.2.0/zh-cn.ttf)

### 配置

#### 配置文件

打开软件->设置->配置->设置配置->打开文件 , 修改合适的代理端口、服务端名称和命令，默认文件见[config.json](https://github.com/ElementAstro/HEAL/blob/main/config/config.json)

#### 代理设置

打开软件->设置->代理 , 根据需要调整代理设置

### 下载

#### 官方

前往下载页根据提示下载(仅支持 Fiddler、Mitmdump、Lunarcore)

![image](https://github.com/ElementAstro/HEAL/assets/77842352/8def8337-81b7-436c-9f65-1d939357201a)

#### 本地

根据需要可以自行下载文件后放入相应文件夹内

### 启动

#### 第一步

选择合适的服务端后点击一键启动

#### 第二步(可选)

对于部分需要额外启动代理软件的 , 如 Fiddler、Mitmdump , 打开软件->设置->代理 , 选择相应软件后打开即可

#### 第三步(可选)

对于关闭服务端后存在未关闭代理设置的 , 打开软件->设置->代理->重置代理->重置 , 可一键关闭
