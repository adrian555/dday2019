if [ "${RUN_SPARK_AS}" = "master" ];
  then bash -c "${SPARK_HOME}/sbin/start-master.sh";
  else bash -c "${SPARK_HOME}/sbin/start-slave.sh ${SPARK_MASTER}"; 
fi
