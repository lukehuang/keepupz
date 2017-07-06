pipeline {
  agent any
  stages {
    stage('build') {
      steps {
        sh '''dt=$(date '+%Y.%m.%d.%H.%M')
docker build --rm -t ispm/keepupz:$dt .
mkdir -p img_out
docker save -o ispm_keepupz_$dt.tar ispm/keepupz:$dt
mv ispm_keepupz_$dt.tar img_out/
echo $dt > img_out/version'''
      }
    }
    stage('test') {
      steps {
        sh '''VERSION=`cat img_out/version`
docker run --rm ispm/keepupz:$VERSION python tests.py
git remote add github git@github.com:ISPM/keepupz.git
git tag -a $VERSION -m "Jenkins auto build $VERSION"
git push github tag $VERSION'''
      }
    }
    stage('S3') {
      steps {
        sh '''VERSION=`cat img_out/version`
gzip img_out/ispm_keepupz_$VERSION.tar
aws s3 cp img_out/ispm_keepupz_$VERSION.tar.gz s3://ispm-artifacts-repository/docker/keepupz/ --content-type="application/x-gzip"'''
      }
    }
  }
}