#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# Author: Sudem mail@szhcloud.cn
# 写在项目最前面的话
#
# 非常感谢宝塔团队给予了我这个平台，这是我在2019年暑假结束前的最后一个作品
# 这个暑假我学习了很多，收获了很多，过的非常的充实
# 我将继续努力下去，成功一个优秀的小码农
#
# 鸣谢 github 大佬 houtianze  https://github.com/houtianze/bypy
# 您的 bypy 项目给予我学习百度api 开发的机会
# 您是 baidu 网盘在linux 界面的先驱者,为了表示对您的感谢,传达 开源、互助的精神
# 本项目BDpan 在 github 开源，并使用MIT 授权，允许任何人在此基础上进行修改
#
# 感谢 运维巨巨、前端郭尧，我的好舍友强哥、鲍哥
# 好兄弟的支持是我成长的道路上最大的动力

#--------------------------------------------------------------------

import os,json,requests,base64,sys,datetime,getopt,math
import logging,warnings
logging.basicConfig(level = logging.INFO,format = '%(asctime)s %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


#设置运行目录
os.chdir("/www/server/panel")
#添加包引用位置并引用公共包
sys.path.append("class/")
import public

class BDpan:

    # 设置本项目的百度云 API KEY
    _client_id = "nIoc7T7GA953ao9LWfd53zGf"
    _token = ""


    #|@ token 百度api授权的json文件的地址,默认 /www/server/panel/plugin/baidupan/baidu.json
    def __init__(self,token="/www/server/panel/plugin/baidupan/baidu.json"):
        self._token = token
        pass

    #返回前端需要访问的认证地址
    # |@ callback   百度api授权成功后，iw3c授权中心回调的地址
    # |@ usertoken  用户客户端的usertoken(设备标识代码)
    # |@ authparam  鉴权加密效验参数 16位随机字符串
    # |@ authtoken  鉴权密钥，算法 md5( usertoken + userkey + authparam)
    def BaiDuAuth(self,args):
        auth  = "callback="+args.callback + "&usertoken="+args.usertoken+ "&authparam="+args.authparam + "&authtoken=" + args.authtoken
        auth = base64.b64encode(auth.encode()).decode()
        api = "https://openapi.baidu.com/oauth/2.0/authorize"
        param = "?response_type=code&client_id=" +self._client_id + "&redirect_uri=https%3a%2f%2fauth.iw3c.top%2f%3fapi%3dbaidupan&state=" +auth +"&scope=basic netdisk"
        url = api + param
        return url



    # 获得Access_Token
    # 注意百度授权规定，开发者每月需要更新一次access_token
    # 为了避免时差等因素影响，这里每10天刷新一次
    def Get_Access_Token(self):
        auth=json.loads(public.ReadFile(self._token))
        if 'AC_Time' in auth:
            AC_Time = datetime.datetime.strptime(auth['AC_Time'],"%Y-%m-%d")
            Now_time =  datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d'),"%Y-%m-%d")
            if Now_time > AC_Time:
                self.Reflush_Access_Token()
                return self.Get_Access_Token()
        else:
            auth['AC_Time'] = (datetime.datetime.now() + datetime.timedelta(days =10)).strftime('%Y-%m-%d')
            public.WriteFile(self._token,json.dumps(auth))
        return auth['access_token']

    # 刷新Access_Token
    def Reflush_Access_Token(self):
        auth = json.loads(public.ReadFile(self._token))
        url = "http://auth.iw3c.top/?api=baidutoken&f=reflush&token="+auth['refresh_token']
        auth = json.loads(requests.get(url,verify=False).text)
        auth['AC_Time'] = (datetime.datetime.now() + datetime.timedelta(days=10)).strftime('%Y-%m-%d')
        public.WriteFile(self._token, json.dumps(auth))

    # 获取百度用户信息
    def Get_UserData(self):
        url = "https://pan.baidu.com/rest/2.0/xpan/nas?method=uinfo"+"&access_token="+self.Get_Access_Token()
        UserData = requests.get(url,verify=False).text
        return UserData

    # 获取百度磁盘容量信息
    def Get_UserDisk(self):
        url = "https://pan.baidu.com/api/quota?access_token="+self.Get_Access_Token()
        DISK = requests.get(url,verify=False).text
        return DISK

    # 获得指定目录的信息
    def Get_PathDir(self,args):
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=list"
        param = "&dir=" + args.path + "&start=" + args.start + "&limit=10000&folder=0"+"&access_token="+self.Get_Access_Token()
        param = param.replace("+","%2b")
        Dir = requests.get(api+param,verify=False).text
        return Dir

    # 下载指定的文件
    def FileDownLoad(self,path,fid):
        api = "https://pan.baidu.com/rest/2.0/xpan/multimedia?method=filemetas"
        param = "&fsids=["+fid+"]"+"&dlink=1&access_token="+self.Get_Access_Token()
        File = requests.get(api + param, verify=False).text
        dlink = json.loads(File)['list'][0]['dlink']+"&access_token="+self.Get_Access_Token()
        os.popen("wget -d --header=\"User-Agent: pan.baidu.com\" \""+dlink+"\" -O \""+path+"\"")

    # 删除指定的文件
    def FileDel(self,path):
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=delete&access_token=" + self.Get_Access_Token()
        param = {"async":1,"filelist":"[\""+path+"\"]"}
        headers = {"User-Agent":"pan.baidu.com"}
        Res=  requests.post(url=api,data=param,headers=headers,verify=False).text
        return Res

    # 重命名指定的文件
    def FileRename(self,path,name):
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=rename&access_token=" + self.Get_Access_Token()
        param = {"async":1,"filelist":"[{\"path\":\""+path+"\",\"newname\":\""+name+"\"}]","ondup":"overwrite"}
        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        return Res

    # 复制指定的文件
    def FileCopy(self,path,dest,name):
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=copy&access_token=" + self.Get_Access_Token()
        param = { "async": 1,"filelist": "[{\"path\":\"" + path + "\",\"dest\":\"" + dest + "\",\"newname\":\""+name+"\"}]", "ondup": "overwrite"}
        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        return Res

    # 移动（剪切）指定的文件
    def FileMove(self,path,dest,name):
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=filemanager&opera=move&access_token=" + self.Get_Access_Token()
        param = {"async": 1, "filelist": "[{\"path\":\"" + path + "\",\"dest\":\"" + dest + "\",\"newname\":\"" + name + "\"}]", "ondup": "overwrite"}
        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        return Res

    # 上传 文件接口
    def FileUpload(self,lpath,spath,move):
        lsize = os.path.getsize(lpath)
        lname = os.path.basename(lpath)
        if move == "move":
            sspath = spath
            spath = "/apps/BTBD/"+lname
        split=json.loads(self.FileSlipt(lpath))
        block_list = []
        cut = 1
        while cut != split["bags"] + 1:
            md5 = public.FileMd5("/PythonFileSplit/"+split["fid"]+"/"+split["fid"]+"_"+str(cut)+".cut")
            block_list.append(md5)
            cut = cut + 1
        block_list = json.dumps(block_list)
        # 与上传
        api = " https://pan.baidu.com/rest/2.0/xpan/file?method=precreate&access_token=" + self.Get_Access_Token()
        param = {"path":spath,"size":lsize,"isdir":0,"autoinit":1,"block_list":block_list}

        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        self.LogPrint("预上传响应")
        self.LogPrint(Res)
        Precreate = json.loads(Res)
        if Precreate["errno"]!= 0:
            self.LogPrint("[致命错误]预上传文件失败！")

        # 开始分片上传文件
        cut = 1
        while cut != split["bags"] + 1:
            per= str(round(float(cut) / float(split["bags"]) * 100,2))
            self.LogPrint("分片上传 任务[" + str(cut) + "/" + str(split["bags"]) +"]("+per + "%)")
            api = "https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?access_token=" + self.Get_Access_Token()+"&method=upload&type=tmpfile&path="+spath+"&uploadid="+Precreate["uploadid"]+"&partseq="+str(cut-1)
            tpath ="/PythonFileSplit/"+split["fid"]+"/"+split["fid"]+"_"+str(cut)+".cut"
            ctry = 1
            self.FileSplitUpload(api,tpath,ctry,block_list,cut)
            self.LogPrint("分片上传成功!")
            cut = cut + 1
        os.popen("rm -rf "+"/PythonFileSplit/"+split["fid"])
        # 分片上传结束 开始创建文件
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token=" + self.Get_Access_Token()
        param = {"path": spath, "size": lsize, "isdir": 0, "uploadid": Precreate["uploadid"],"block_list":block_list}
        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        self.LogPrint("文件创建响应")
        self.LogPrint(Res)
        if json.loads(Res)["errno"] ==0:
            self.LogPrint("文件上传成功!")
            if move =="move":
                self.LogPrint("移动文件中...")
                self.FileMove("/apps/BTBD/"+lname,sspath,lname)
                self.LogPrint("文件移动成功...")
        else:self.LogPrint("文件上传失败!")


    #切片后的文件上传
    def FileSplitUpload(self,api,tpath,ctry,block_list,cut):
        try:
            upfile = open(tpath, 'rb');
            files = {'file': open(tpath, 'rb')}
            Res = requests.post(url=api, files=files, verify=False).text
            if json.loads(Res)["md5"] !="":
                self.LogPrint(Res)
        except:
            upfile.close()
            if ctry <= 3:
                self.LogPrint("上传失败,正在重试中...")
                ctry = ctry + 1
                self.FileSplitUpload(api,tpath,ctry,block_list,cut)
            else:
                self.LogPrint("三次尝试后，文件上传失败...")
                exit()


    # 文件切片处理
    def FileSlipt(self,lpath,csize = 4096):
        csize = csize*1024
        f = open(lpath,"rb")
        # 生成文件识别编码
        fid = public.GetRandomString(16)
        # 统计需要切片数量
        bags =  int(math.ceil(float(os.path.getsize(lpath))/float(csize)))
        cut = 1
        if not os.path.exists("/PythonFileSplit"):
            os.mkdir("/PythonFileSplit")
        os.mkdir("/PythonFileSplit/"+fid)
        while cut != bags+1:
            c = open("/PythonFileSplit/"+fid+"/"+fid+"_"+str(cut)+".cut","wb")
            fdata = f.read(csize)
            c.write(fdata)
            c.close()
            cut = cut + 1
        return json.dumps({"fid":fid,"bags":bags})

    # 新建文件夹
    def FilePathAdd(self,path):
        # 分片上传结束 开始创建文件
        api = "https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token=" + self.Get_Access_Token()
        param = {"path":path, "size": 0, "isdir": 1}
        headers = {"User-Agent": "pan.baidu.com"}
        Res = requests.post(url=api, data=param, headers=headers, verify=False).text
        return Res

    def LogPrint(self,msg):
        logger.info(msg)




# 命令行模式
if __name__ == '__main__':

    RunMode = ""
    FilePath = ""
    FileID = ""
    FileUpLoad = ""
    UploadPath = ""
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv, "hdmup:f:s:")
    except getopt.GetoptError:
        print 'Using BDpan.py with Param \n-d [DownLoadFile] \n-u [UploadFile] \n-p <Upload/DownLoad File Path> \n-f <Baidu Pan FileID,Used Only In DownLoad Mode> \n-s <Baidu Pan FilePath,Used Only In Upload Mode> \n-m <Move File When Upload Success>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Using BDpan.py with Param \n-d [DownLoadFile] \n-u [UploadFile] \n-p <Upload/DownLoad File Path> \n-f <Baidu Pan FileID,Used Only In Download Mode> \n-s <Baidu Pan FilePath,Used Only In Upload Mode> \n-m <Move File When Upload Success>'
            sys.exit()
        elif opt == '-d': RunMode = "DownLoad"
        elif opt == '-u': RunMode = "Upload"
        elif opt == '-p': FilePath = arg
        elif opt == '-f': FileID = arg
        elif opt == '-s': UploadPath = arg
        elif opt == "-m": FileUpLoad = "move"

    BD = BDpan()
    if RunMode == "DownLoad":
        BD.FileDownLoad(FilePath, FileID)
    elif RunMode == "Upload":
        BD.FileUpload(FilePath,UploadPath,FileUpLoad)
    else:
        print "UnKnow Running Mode!"
        sys.exit(2)


















