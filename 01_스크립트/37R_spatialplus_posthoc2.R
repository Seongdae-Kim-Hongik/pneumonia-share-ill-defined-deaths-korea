#  사용: ST_THREADS=1 ST_GRAPH=<593> ./rslot.sh Rscript 37R_spatialplus_posthoc2.R   산출: results_std3/S41_spatialplus_OR.csv, S47_posthoc_chewing.csv
suppressPackageStartupMessages({library(INLA);library(sf);library(jsonlite)})
ROOT<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),".."))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
OUTD<-file.path(ROOT,"04_분석","RESP");RES<-file.path(OUTD,"results_std3");inla.setOption(num.threads="1:1")
S<-fromJSON(file.path(OUTD,"config_RESP_std3.json"),simplifyVector=TRUE);FORCED<-S$forced;HYP<-as.character(S$sets_after_vif[["S1_narrative_full"]])
DD<-read.csv(file.path(OUTD,"panel_RESP_binom_std3.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region);g<-inla.read.graph(Sys.getenv("ST_GRAPH"))
DD$area<-match(DD$fbd_region,G$region);DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time;stopifnot(!anyNA(DD$area))
FAM<-{lk<-read.csv(file.path(RES,"S1_likelihood.csv"));lk$family[which.min(lk$WAIC)]}
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
RE<-c("f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc)","f(time,model='rw1',scale.model=TRUE,hyper=pcp)","f(yiid,model='iid',hyper=pcp)")
fit<-function(v,data){f<-as.formula(paste("pneu ~",paste(c("1",sprintf("`%s`",v),RE,"offset(off_pc)"),collapse="+")))
  inla(f,family=FAM,Ntrials=data$n_pc,data=data,control.fixed=list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001),control.compute=list(waic=TRUE),control.inla=list(int.strategy="eb"),verbose=FALSE)}
tab<-function(m,spec){r<-m$summary.fixed;r<-r[rownames(r)!="(Intercept)",];data.frame(spec=spec,cov=rownames(r),OR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),cred=(r$`0.025quant`>0|r$`0.975quant`<0),WAIC=round(m$waic$waic,1))}
# 그래프 라플라시안
A<-matrix(0,g$n,g$n);for(i in 1:g$n){if(g$nnbs[i]>0)A[i,g$nbs[[i]]]<-1};A<-pmax(A,t(A));L<-diag(rowSums(A))-A;e<-eigen(L,symmetric=TRUE)
ord<-order(e$values);K<-23;nz<-ord[e$values[ord]>1e-8][1:K];E<-e$vectors[,nz]
SP<-DD;for(v in HYP){X<-E[SP$area,,drop=FALSE];r<-resid(lm(SP[[v]]~X));SP[[v]]<-(r-mean(r))/sd(r)}
o<-rbind(tab(fit(c(FORCED,HYP),SP),"spatial_plus"))
write.csv(o,file.path(RES,"S41_spatialplus_OR.csv"),row.names=FALSE)
o2<-tab(fit(c(FORCED,"chewing_discomfort_rate_65plus"),DD),"P6_chewing_alone")
write.csv(o2,file.path(RES,"S47_posthoc_chewing.csv"),row.names=FALSE);cat("done\n")
