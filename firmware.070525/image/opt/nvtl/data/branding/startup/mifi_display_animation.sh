#!/bin/sh
#
# splash_animation
#

export PATH=$PATH:/opt/nvtl/bin
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/nvtl/lib

BASE_PATH=/opt/nvtl/data/branding/startup/animation_
NUM_FILES=65
USLEEP=99000
NUM_ITRS=3
MAX_NUM_FILES=166
ONE=1

cache_files()
{
        COUNT=1
        ITR=1
        while [ $ITR -lt $NUM_ITRS ]; do
                if [ $ITR -eq 1 ]; then
                        dd if=$BASE_PATH$COUNT.png of=/dev/null bs=32K > /dev/null 2>&1
                else
                        if [ ! -L $BASE_PATH$COUNT.png ]; then
                                if [ $(( $COUNT%$NUM_FILES )) -eq 0 ]; then
                                        ln -s $BASE_PATH$ONE.png $BASE_PATH$COUNT.png
                                else
                                        ln -s $BASE_PATH$(( $COUNT%$NUM_FILES )).png $BASE_PATH$COUNT.png
                                fi
                        fi
                fi

                if [ $(( $COUNT%$NUM_FILES )) -eq 0 ]; then
                        let ITR=ITR+1
                fi
                let COUNT=COUNT+1
        done
}

case $1 in

        start)
                echo "power on animation cache files started" > /dev/kmsg
		cache_files
                echo "[MIFI_TIMESTAMP] - power on animation started" > /dev/kmsg
                chrt -f 1 /opt/nvtl/bin/mifi_display_png  $BASE_PATH $NUM_FILES $USLEEP &
                ;;

        stop)
                echo "stopping splashscreen animation"
                killall -q mifi_display_png
		;;
esac
