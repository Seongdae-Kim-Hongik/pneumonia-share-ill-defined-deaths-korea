# 37R — RESP 사인 구성(폐렴 ÷ (폐렴 + CLRD)) 이항 시공간 체인(2026-11-12, 새 파일; 81_fit_inla.R의 그래프·사전분포·1스레드 규칙을 그대로 따름).
#  사용(01_스크립트/): ST_THREADS=1 ST_GRAPH=<593> MODE=main|mv|win|sens Rscript 37R_fit_binom.R   (모든 실행은 rslot.sh 경유)
#  모형: pneu ~ Binomial(n_pc, p), logit p = offset(logit p0) + 1 + X + f(area,bym2) + f(time,rw1) + f(yiid,iid)
#   S1 우도(forced-only binomial vs betabinomial) · M1 주모형(S1 세트) · NC 음성대조 · 대안 세트 S2~S4
#   M2a/M2b 이동 속도: + f(area2, tc, bym2) (tc = (year-2017.5)/10) · M3 속도 결정요인: + 기준선(2011-13 평균) 가설 변수 × tc
#   DEC 지역 간·내 분해 · WIN 창별 · SENS(분모 J00-J98, CLRD 결과, 1년 지연, 2020-22 제외, + 노쇠, + 관외 외래, offset 없음, 그래프 577)
#   MV 다중우주(MV_RANGE=a-b, 강제 5 고정 + 가설 부분집합, seed 37; 베타이항 1개 5분 → 하이퍼파라미터 int.strategy="eb", 주모형 대비 검산은 mv000 = 전체 세트)
suppressPackageStartupMessages({library(INLA);library(sf);library(spdep);library(jsonlite)})
ROOT<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),".."))
SHP<-Sys.getenv("ST_SHP",file.path(normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..")),"data","boundary","final.shp"))
TAG<-"RESP";OUTD<-file.path(ROOT,"04_분석",TAG);RES<-file.path(OUTD,"results_std3");dir.create(RES,showWarnings=FALSE)
inla.setOption(num.threads=sprintf("%s:1",Sys.getenv("ST_THREADS",unset="1")))
MODE<-Sys.getenv("MODE",unset="main")
LOG<-function(...)cat(sprintf("[37R %s %s] ",MODE,format(Sys.time(),"%H:%M:%S")),sprintf(...),"\n",sep="")
S<-fromJSON(file.path(OUTD,"config_RESP_std3.json"),simplifyVector=TRUE)
META<-read.csv(file.path(OUTD,"panel_META_RESP_std3.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE)
DD<-read.csv(file.path(OUTD,"panel_RESP_binom_std3.csv"),fileEncoding="UTF-8-BOM",stringsAsFactors=FALSE);DD$fbd_region<-enc2utf8(DD$fbd_region)
FORCED<-S$forced;NEG<-S$negative_controls;SETS<-lapply(S$sets_after_vif,as.character);HYP<-SETS[["S1_narrative_full"]]
stopifnot(all(c(FORCED,HYP,NEG,"outside_care_share","senility_share")%in%names(DD)))
G<-st_read(SHP,quiet=TRUE);G$region<-enc2utf8(G$region)
mkgraph<-function(use_ext){nb<-poly2nb(G,queen=TRUE);isl<-which(card(nb)==0)
  if(length(isl)){cen<-st_coordinates(st_centroid(st_geometry(G)));kn<-knearneigh(cen,k=1)$nn
    for(i in isl){j<-kn[i,1];nb[[i]]<-sort(unique(c(nb[[i]][nb[[i]]>0],j)));nb[[j]]<-sort(unique(c(nb[[j]][nb[[j]]>0],i)))}}
  if(use_ext){sg<-inla.read.graph(Sys.getenv("ST_GRAPH"));stopifnot(sg$n==nrow(G));for(i in seq_len(sg$n))nb[[i]]<-as.integer(sort(sg$nbs[[i]]));attr(nb,"sym")<-TRUE}
  f<-tempfile(fileext=".graph");nb2INLA(f,nb);list(g=inla.read.graph(f),nb=nb,links=sum(card(nb))/2)}
GR<-mkgraph(nzchar(Sys.getenv("ST_GRAPH")));g<-GR$g;LOG("graph links %d",GR$links)
DD$area<-match(DD$fbd_region,G$region);stopifnot(!anyNA(DD$area));DD$area2<-DD$area;DD$time<-DD$year-min(DD$year)+1;DD$yiid<-DD$time;DD$id<-seq_len(nrow(DD))
DD$tc<-(DD$year-2017.5)/10
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
CF<-list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001)
SP<-"f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc)";TI<-"f(time,model='rw1',scale.model=TRUE,hyper=pcp)";IT<-"f(yiid,model='iid',hyper=pcp)"
SL<-"f(area2,tc,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc)"
bt<-function(v)sprintf("`%s`",v)
FAM<-"binomial";lkf<-file.path(RES,"S1_likelihood.csv");if(file.exists(lkf)){lk<-read.csv(lkf);FAM<-lk$family[which.min(lk$WAIC)]}
fitb<-function(vars,data=DD,y="pneu",n="n_pc",off="off_pc",extra=character(0),re=c(SP,TI,IT),fam=FAM,robust=FALSE,cpo=TRUE,cfg=FALSE,eb=FALSE){
  rhs<-c("1",bt(vars),extra,re,if(!is.null(off))sprintf("offset(%s)",off));form<-as.formula(paste(y,"~",paste(rhs,collapse="+")))
  ci<-if(robust)list(control.vb=list(emergency=50),int.strategy="eb",strategy="gaussian") else if(eb)list(control.vb=list(emergency=50),int.strategy="eb") else list(control.vb=list(emergency=50))
  inla(form,family=fam,Ntrials=data[[n]],data=data,control.fixed=CF,control.compute=list(dic=TRUE,waic=TRUE,cpo=cpo,config=cfg),control.inla=ci,verbose=FALSE)}
safe<-function(...)tryCatch(fitb(...),error=function(e){message("  fit failed: ",conditionMessage(e)," -> robust");tryCatch(fitb(...,robust=TRUE),error=function(e2){message("  retry failed: ",conditionMessage(e2));NULL})})
orr<-function(m,v,tag=""){r<-m$summary.fixed[v,,drop=FALSE];data.frame(model=tag,cov=v,OR=round(exp(r$mean),4),lo=round(exp(r$`0.025quant`),4),hi=round(exp(r$`0.975quant`),4),
  P_gt1=round(1-inla.pmarginal(0,m$marginals.fixed[[v]]),3),cred=(r$`0.025quant`>0|r$`0.975quant`<0),stringsAsFactors=FALSE)}
fst<-function(m,tag){cp<-m$cpo$cpo;h<-m$summary.hyperpar;data.frame(model=tag,family=FAM,WAIC=round(m$waic$waic,1),DIC=round(m$dic$dic,1),LCPO=round(-mean(log(cp[is.finite(cp)&cp>0])),4),cpo_fail=sum(m$cpo$failure>0,na.rm=TRUE),
  phi_area=round(if("Phi for area"%in%rownames(h))h["Phi for area","mean"] else NA,3),phi_slope=round(if("Phi for area2"%in%rownames(h))h["Phi for area2","mean"] else NA,3),
  sd_slope=round(if("Precision for area2"%in%rownames(h))1/sqrt(h["Precision for area2","mean"]) else NA,4),rho_bb=round(if(any(grepl("overdispersion",rownames(h))))h[grep("overdispersion",rownames(h))[1],"mean"] else NA,4))}
wcsv<-function(x,f)write.csv(x,file.path(RES,f),row.names=FALSE,fileEncoding="UTF-8")
done<-function(f)file.exists(file.path(RES,f))
tm<-function(lab,expr){t0<-Sys.time();r<-expr;LOG("%s %.1f min",lab,as.numeric(difftime(Sys.time(),t0,units="mins")));r}

if(MODE=="main"){
  if(!done("S1_likelihood.csv")){lk<-do.call(rbind,lapply(c("binomial","betabinomial"),function(f){m<-tm(paste("forced-only",f),fitb(FORCED,fam=f));x<-fst(m,"REF_forced_only");x$family<-f;x}))
    wcsv(lk,"S1_likelihood.csv");FAM<-lk$family[which.min(lk$WAIC)]};LOG("family = %s",FAM)
  if(!done("S3_main_OR.csv")){m1<-tm("M1 main",fitb(c(FORCED,HYP),cfg=FALSE));or<-do.call(rbind,lapply(c(HYP,FORCED),function(v)orr(m1,v,"M1")));or$role<-ifelse(or$cov%in%FORCED,"forced","hypothesis")
    or$label_en<-META$label_en[match(or$cov,META$variable)];or$expected<-META$expected_direction[match(or$cov,META$variable)];wcsv(or,"S3_main_OR.csv");wcsv(fst(m1,"M1"),"S3_main_fit.csv")
    re<-m1$summary.random$area[1:nrow(G),];wcsv(data.frame(fbd_region=G$region,re_total=re$mean,OR_area=exp(re$mean),P_gt0=sapply(1:nrow(G),function(i)1-inla.pmarginal(0,m1$marginals.random$area[[i]]))),"S3_area_M1.csv")
    wcsv(data.frame(year=sort(unique(DD$year)),rw1=m1$summary.random$time$mean,iid=m1$summary.random$yiid$mean),"S3_time_M1.csv")
    DD$fit_M1<-m1$summary.fitted.values$mean;wcsv(DD[,c("year","fbd_region","pneu","clrd","n_pc","p0","fit_M1")],"S3_fitted_M1.csv")}
  if(!done("S3_negctrl_OR.csv")){nc<-do.call(rbind,lapply(NEG,function(v){m<-safe(c(FORCED,HYP,v));orr(m,v,paste0("M1+",v))}));wcsv(nc,"S3_negctrl_OR.csv")}
  if(!done("S2_setcompare.csv")){sc<-NULL;ors<-NULL;for(sn in names(SETS)){if(grepl("obesity",sn))next;m<-tm(sn,safe(c(FORCED,SETS[[sn]])));sc<-rbind(sc,cbind(set=sn,fst(m,sn)));ors<-rbind(ors,do.call(rbind,lapply(SETS[[sn]],function(v)orr(m,v,sn))))}
    wcsv(sc,"S2_setcompare.csv");wcsv(ors,"S2_setcompare_OR.csv")}
  for(sp in list(list("M2a",FORCED),list("M2b",c(FORCED,HYP)))){nm<-sp[[1]];if(done(sprintf("S20_speed_%s_area.csv",nm)))next
    m<-tm(nm,fitb(sp[[2]],extra=SL));n<-nrow(G);r<-m$summary.random$area2
    a<-data.frame(fbd_region=G$region,delta=r$mean[1:n],lo=r$`0.025quant`[1:n],hi=r$`0.975quant`[1:n],P_gt0=sapply(1:n,function(i)1-inla.pmarginal(0,m$marginals.random$area2[[i]])),
      struct=r$mean[(n+1):(2*n)],level_re=m$summary.random$area$mean[1:n])
    wcsv(a,sprintf("S20_speed_%s_area.csv",nm));wcsv(fst(m,nm),sprintf("S20_speed_%s_fit.csv",nm))
    if(nm=="M2b")wcsv(do.call(rbind,lapply(c(HYP,FORCED),function(v)orr(m,v,nm))),"S20_speed_M2b_OR.csv")}
  if(!done("S21_speed_determinants_OR.csv")){B<-DD[DD$year<=2013,];bm<-aggregate(B[,HYP],list(fbd_region=B$fbd_region),mean)
    for(v in HYP){z<-bm[[v]];bm[[v]]<-(z-mean(z))/sd(z)};X<-merge(DD,setNames(bm,c("fbd_region",paste0("b0_",HYP))),by="fbd_region",sort=FALSE);X<-X[order(X$id),]
    for(v in HYP)X[[paste0("bx_",v)]]<-X[[paste0("b0_",v)]]*X$tc
    m<-tm("M3",fitb(c(FORCED,HYP,paste0("bx_",HYP)),data=X,extra=SL));o<-do.call(rbind,lapply(c(paste0("bx_",HYP),HYP),function(v)orr(m,v,"M3")))
    o$per<-ifelse(grepl("^bx_",o$cov),"OR per SD of 2011-13 baseline per decade (speed)","OR per SD (level)");wcsv(o,"S21_speed_determinants_OR.csv");wcsv(fst(m,"M3"),"S21_speed_determinants_fit.csv")}
  if(!done("S22_decomp_OR.csv")){X<-DD;bvars<-c();for(v in HYP){mu<-ave(X[[v]],X$fbd_region);X[[paste0("bw_",v)]]<-mu;X[[paste0("wi_",v)]]<-X[[v]]-mu;bvars<-c(bvars,paste0("bw_",v),paste0("wi_",v))}
    m<-tm("DEC",fitb(c(FORCED,bvars),data=X));wcsv(do.call(rbind,lapply(bvars,function(v)orr(m,v,"DEC"))),"S22_decomp_OR.csv")}
  LOG("main done")}

if(MODE=="win"&&!done("S4_window_OR.csv")){o<-NULL;W<-list(W1=c(2011,2015),W2=c(2016,2019),W3=c(2020,2024))
  for(w in names(W)){X<-DD[DD$year>=W[[w]][1]&DD$year<=W[[w]][2],];X$time<-X$year-min(X$year)+1;X$yiid<-X$time;m<-tm(w,safe(c(FORCED,HYP),data=X));o<-rbind(o,do.call(rbind,lapply(HYP,function(v)orr(m,v,w))))}
  wcsv(o,"S4_window_OR.csv")}

if(MODE=="sens"&&!done("S40_sens_OR.csv")){o<-NULL;fs<-NULL;add<-function(m,tag,vars=HYP){if(is.null(m))return();o<<-rbind(o,do.call(rbind,lapply(intersect(vars,rownames(m$summary.fixed)),function(v)orr(m,v,tag))));fs<<-rbind(fs,fst(m,tag))}
  add(tm("denomJ00-98",safe(c(FORCED,HYP),n="resp",off="off_r")),"SN1_pneu_of_all_resp")
  add(tm("CLRD outcome",safe(c(FORCED,HYP),y="clrd",n="resp",off="off_cr")),"SN2_clrd_of_all_resp")
  X<-DD[order(DD$fbd_region,DD$year),];for(v in HYP)X[[v]]<-ave(X[[v]],X$fbd_region,FUN=function(s)c(NA,head(s,-1)));X<-X[X$year>2011,];X<-X[order(X$id),];X$time<-X$year-min(X$year)+1;X$yiid<-X$time
  add(tm("lag1",safe(c(FORCED,HYP),data=X)),"SN3_lag1")
  X<-DD[!DD$year%in%2020:2022,];X$time<-match(X$year,sort(unique(X$year)));X$yiid<-X$time;add(tm("noCOVID",safe(c(FORCED,HYP),data=X)),"SN4_excl_2020_22")
  add(tm("+senility",safe(c(FORCED,HYP,"senility_share"))),"SN5_plus_senility",c(HYP,"senility_share"))
  add(tm("+outside",safe(c(FORCED,HYP,"outside_care_share"))),"SN6_plus_outside_care",c(HYP,"outside_care_share"))
  add(tm("no offset",safe(c(FORCED,HYP),off=NULL)),"SN7_no_age_offset")
  g577<-mkgraph(FALSE);LOG("graph577 links %d",g577$links);gsave<-g;g<-g577$g;add(tm("g577",safe(c(FORCED,HYP))),"SN8_graph577");g<-gsave
  wcsv(o,"S40_sens_OR.csv");wcsv(fs,"S40_sens_fit.csv")}

if(MODE=="mv"){rg<-as.integer(strsplit(Sys.getenv("MV_RANGE",unset="1-200"),"-")[[1]]);set.seed(37);NS<-200
  SPEC<-lapply(1:NS,function(i){k<-runif(length(HYP))<0.5;if(!any(k))k[sample(length(HYP),1)]<-TRUE;HYP[k]})
  f<-sprintf("S7_mv_%03d_%03d.csv",rg[1],rg[2]);if(!done(f)){o<-NULL
    if(rg[1]==1){m<-safe(c(FORCED,HYP),cpo=FALSE,eb=TRUE);x<-do.call(rbind,lapply(HYP,function(v)orr(m,v,"mv000_full_eb")));x$spec<-0;wcsv(x,"S7_mv_000_full_eb.csv")}
    for(i in rg[1]:rg[2]){m<-safe(c(FORCED,SPEC[[i]]),cpo=FALSE,eb=TRUE);if(is.null(m))next;x<-do.call(rbind,lapply(SPEC[[i]],function(v)orr(m,v,sprintf("mv%03d",i))));x$spec<-i;o<-rbind(o,x);if(i%%10==0)LOG("mv %d",i)}
    wcsv(o,f)}}
LOG("exit")
