# 37R — RESP 역방향 사후 검정(post hoc, 결과를 본 뒤 수행; 2026-11-12 새 파일). 플레이북 15 역방향 절차 2단계.
#  대상: 현재흡연율(주모형 OR 1.022, 가설 −), 요양병원/65+(지역 간 0.925, 가설 +)
#  P1 흡연 단독 + 강제 5 / P2 흡연 → 폐암 진료 log SIR(기준 SQLite disease_panel LCA, 누적 흡연 노출의 객관 대리)로 대체 / P3 요양병원 단독 + 강제 5
#  P4 주모형 − 흡연(다른 계수 변화 확인) / P5 흡연 + 폐암 log SIR 동시
#  사용: ST_THREADS=1 ST_GRAPH=<593> ./rslot.sh Rscript 37R_posthoc_reverse.R   산출: results_std3/S46_posthoc_reverse.csv
suppressPackageStartupMessages({library(INLA);library(sf);library(jsonlite);library(DBI);library(RSQLite)})
ROOT<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),".."))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
SQ<-file.path(Sys.getenv("ST_DATASET_ROOT"),"연구데이터셋_5종_GPT버전/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite")
OUTD<-file.path(ROOT,"04_분석","RESP");RES<-file.path(OUTD,"results_std3");inla.setOption(num.threads="1:1")
S<-fromJSON(file.path(OUTD,"config_RESP_std3.json"),simplifyVector=TRUE);FORCED<-S$forced;HYP<-as.character(S$sets_after_vif[["S1_narrative_full"]])
DD<-read.csv(file.path(OUTD,"panel_RESP_binom_std3.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
con<-dbConnect(SQLite(),SQ,flags=SQLITE_RO);L<-dbGetQuery(con,"select year, fbd_region, cases, E from disease_panel where tag='LCA'");dbDisconnect(con)
L$fbd_region<-enc2utf8(L$fbd_region);L$lca_logsir<-log(L$cases/L$E);DD<-merge(DD,L[,c("year","fbd_region","lca_logsir")],by=c("year","fbd_region"),all.x=TRUE,sort=FALSE)
stopifnot(!anyNA(DD$lca_logsir));DD$lca_logsir<-(DD$lca_logsir-mean(DD$lca_logsir))/sd(DD$lca_logsir);cat("cor(smoking, LCA logSIR) =",round(cor(DD$current_smoking_rate,DD$lca_logsir),3),"\n")
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time
FAM<-{lk<-read.csv(file.path(RES,"S1_likelihood.csv"));lk$family[which.min(lk$WAIC)]}
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
RE<-c("f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc)","f(time,model='rw1',scale.model=TRUE,hyper=pcp)","f(yiid,model='iid',hyper=pcp)")
fit<-function(v){f<-as.formula(paste("pneu ~",paste(c("1",sprintf("`%s`",v),RE,"offset(off_pc)"),collapse="+")))
  inla(f,family=FAM,Ntrials=DD$n_pc,data=DD,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE),control.inla=list(int.strategy="eb"),verbose=FALSE)}
SP<-list(P1_smoking_alone=c(FORCED,"current_smoking_rate"),P2_lca_replaces_smoking=c(FORCED,setdiff(HYP,"current_smoking_rate"),"lca_logsir"),
  P3_ltc_alone=c(FORCED,"ltc_hospitals_per_100k_65"),P4_main_minus_smoking=c(FORCED,setdiff(HYP,"current_smoking_rate")),P5_smoking_plus_lca=c(FORCED,HYP,"lca_logsir"))
o<-NULL;for(n in names(SP)){t0<-Sys.time();m<-fit(SP[[n]]);r<-m$summary.fixed;r<-r[rownames(r)!="(Intercept)",]
  o<-rbind(o,data.frame(spec=n,cov=rownames(r),OR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),cred=(r$`0.025quant`>0|r$`0.975quant`<0),WAIC=round(m$waic$waic,1)))
  cat(n,round(as.numeric(difftime(Sys.time(),t0,units="mins")),1),"min\n")}
write.csv(o,file.path(RES,"S46_posthoc_reverse.csv"),row.names=FALSE);cat("done\n")
