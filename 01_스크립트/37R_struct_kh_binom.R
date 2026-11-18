# 37R — RESP 구조 민감도(Knorr-Held I~IV, 이항/베타이항, 2026-11-12 새 파일). 88k_struct_kh.R의 정의를 이항 우도로 옮김.
#  사용(01_스크립트/): ST_THREADS=1 ST_GRAPH=<593> KH=I|II|III|IV ./rslot.sh Rscript 37R_struct_kh_binom.R
#  I: + f(id, iid) / II: + f(area_i, iid, group=time, rw1) / III: + f(time_i, iid, group=area, besag) / IV: + f(area_i, besag, group=time, rw1)
#  산출: results_std3/S43_KH_<type>_OR.csv, S43_KH_<type>_fit.csv
suppressPackageStartupMessages({library(INLA);library(sf);library(spdep);library(jsonlite)})
ROOT<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),".."))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
OUTD<-file.path(ROOT,"04_분석","RESP");RES<-file.path(OUTD,"results_std3")
inla.setOption(num.threads=sprintf("%s:1",Sys.getenv("ST_THREADS",unset="1")));KH<-Sys.getenv("KH",unset="I")
LOG<-function(...)cat(sprintf("[37R-KH %s %s] ",KH,format(Sys.time(),"%H:%M:%S")),sprintf(...),"\n",sep="")
S<-fromJSON(file.path(OUTD,"config_RESP_std3.json"),simplifyVector=TRUE);FORCED<-S$forced;HYP<-as.character(S$sets_after_vif[["S1_narrative_full"]])
DD<-read.csv(file.path(OUTD,"panel_RESP_binom_std3.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"));stopifnot(g$n==nrow(G))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time;DD$id<-seq_len(nrow(DD));DD$area_i<-DD$area;DD$time_i<-DD$time
FAM<-{lk<-read.csv(file.path(RES,"S1_likelihood.csv"));lk$family[which.min(lk$WAIC)]}
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
CF<-list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001)
base<-c("f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc)","f(time,model='rw1',scale.model=TRUE,hyper=pcp)","f(yiid,model='iid',hyper=pcp)")
INT<-switch(KH,I="f(id,model='iid',hyper=pcp)",
  II="f(area_i,model='iid',group=time_i,control.group=list(model='rw1',scale.model=TRUE),hyper=pcp)",
  III="f(time_i,model='iid',group=area_i,control.group=list(model='besag',graph=g,scale.model=TRUE),hyper=pcp)",
  IV="f(area_i,model='besag',graph=g,scale.model=TRUE,group=time_i,control.group=list(model='rw1',scale.model=TRUE),hyper=pcp)")
form<-as.formula(paste("pneu ~",paste(c("1",sprintf("`%s`",c(FORCED,HYP)),base,INT,"offset(off_pc)"),collapse="+")))
t0<-Sys.time()
m<-tryCatch(inla(form,family=FAM,Ntrials=DD$n_pc,data=DD,control.fixed=CF,control.compute=list(dic=TRUE,waic=TRUE,cpo=FALSE),control.inla=list(control.vb=list(emergency=50),int.strategy="eb",strategy="gaussian"),verbose=FALSE),
  error=function(e){LOG("FAILED %s",conditionMessage(e));NULL})
if(is.null(m))quit(status=1)
LOG("fit %.1f min",as.numeric(difftime(Sys.time(),t0,units="mins")))
o<-do.call(rbind,lapply(c(HYP,FORCED),function(v){r<-m$summary.fixed[v,];data.frame(model=paste0("KH_",KH),cov=v,OR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),cred=(r$`0.025quant`>0|r$`0.975quant`<0))}))
write.csv(o,file.path(RES,sprintf("S43_KH_%s_OR.csv",KH)),row.names=FALSE);write.csv(data.frame(model=paste0("KH_",KH),family=FAM,WAIC=round(m$waic$waic,1),DIC=round(m$dic$dic,1),minutes=round(as.numeric(difftime(Sys.time(),t0,units="mins")),1)),file.path(RES,sprintf("S43_KH_%s_fit.csv",KH)),row.names=FALSE)
LOG("done")
