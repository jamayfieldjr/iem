# Process the apache log files generated from the IEM cluster
# iem
# iemssl
# cocorahs
# datateam
# idep
# schoolnet8
# sustainablecorn
# weatherim
# wepp
# 
# RPM requirements for this workflow
# yum -y install libdb-cxx libmaxminddb gd lftp tcsh tmpwatch

export yyyymmdd="`date --date '1 day ago' +'%Y%m%d'`"
export yyyymm="`date --date '1 day ago' +'%Y%m'`"
export dd="`date --date '1 day ago' +'%d'`"

PREFIXES="iem iemssl cocorahs datateam idep schoolnet8 sustainablecorn weatherim wepp depbackend"
MACHINES="iemvs100 iemvs101 iemvs102 iemvs103 iemvs104 iemvs105 iemvs106 iemvs107 iemvs108 iemvs109"
CONFBASE="/opt/iem/scripts/webalizer"

# Go to temp directory, that hopefully has enough space!
cd /mnt/webalizer/tmp

# Step 1, bring all these log files back to roost and delete them remotely
for MACH in $MACHINES
do
	# limit file transfer to 750Mbit/s
	scp -l 750000 -q root@${MACH}:/mesonet/www/logs/*-${yyyymmdd} .
	ssh root@$MACH "rm -f /mesonet/www/logs/*-${yyyymmdd}"
	# rename the files so that they are unique
	for PREF in $PREFIXES
	do
		if [ -e ${PREF}-${yyyymmdd} ]; then
			mv ${PREF}-${yyyymmdd} ${PREF}-${MACH}.log
		fi
	done
done

for PREF in $PREFIXES
do
	echo "============== $PREF ============="
	wc -l ${PREF}-*.log
	csh -c "(/usr/local/bin/mergelog ${PREF}-*.log > combined-${PREF}.log) >& /dev/null"	
	rm -f ${PREF}-*.log
done

# special step to merge the combined-iem.logs and combined-iemssl.log files
csh -c "(/usr/local/bin/mergelog combined-iem.log combined-iemssl.log > combined.access_log) >& /dev/null"	
rm -f combined-iem.log combined-iemssl.log
mv combined.access_log combined-iem.log

# Step 3, run webalizer against these log files
/home/mesonet/bin/webalizer -c ${CONFBASE}/mesonet.conf -T combined-iem.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/cocorahs.conf combined-cocrahs.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/sustainablecorn.conf combined-sustainablecorn.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/wepp.conf combined-wepp.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/idep.conf combined-idep.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/weatherim.conf combined-weatherim.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/datateam.conf combined-datateam.log
rsync -a /mnt/webalizer/usage/. iem12:/mesonet/share/usage/

grep " /agclimate" combined-iem.log > agclimate.log
/home/mesonet/bin/webalizer -c ${CONFBASE}/agclimate.conf -T agclimate.log
rm -f agclimate.log

# Step 4, archive these files
for PREF in $PREFIXES
do
	if [ -e combined-${PREF}.log ]; then
		mv combined-${PREF}.log ${PREF}-${yyyymmdd}.log
		gzip ${PREF}-${yyyymmdd}.log
	fi
done

lftp -u akrherz@iastate.edu ftps://ftp.box.com << EOM
cd IEMWWWLogs
mkdir $yyyymm
cd $yyyymm
mput *-${yyyymmdd}.log.gz
bye
EOM

mv *-${yyyymmdd}.log.gz ../save/
tmpwatch 10d ../save
# Done!