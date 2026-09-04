C **********************************************************
C                SONO.F        DATE: JUNE 1990
C **********************************************************
C
c  file specialized to deal with imager data on the field computer 
c  at toolik in September, 2015
c  fft choice hard-wired to 8*8192, then skip 9*8*8192, in order
c  to get spectrum per 10s, i.e. roughly page per hour of gray
c  usage: 
c  od -w8 -t u2 -v -A n 20130826-021203-TLK.imager.data | this_program
c
c  before starting need this
c  echo 20130826-021203-TLK.imager.data > filename
c  ls -l 20130826-021203-TLK.imager.data >> filename
      COMPLEX F
      REAL RRDATA
      COMMON/SIGNAL/RDATA(540000)
      COMMON/POWER/F(540000)
      CHARACTER*8 TITLE
      character*40 file1
      integer zlow, zhigh
      character char
      real wfn(540000)
      real B(4,540000),XMAG(4,540000)
      integer*8 leftover
      integer*8 filesize
      real flow(3),fhigh(3)
c needed for two-byte binary read:
      character c2(2)
      integer*2 i2
      INTEGER fgetc,ibb,status
c needed for fseek
      integer :: stati
c needed for ftell
      integer*8 spencer

c needed for two-byte binary read:
      equivalence (i2,c2)
C
      PI = 3.141592654
c      maxdata=-999999
c      mindata=999999
c      nlines=2
c      nlines=300
c
c  open intensity output files...always called "gnudata-N"
c
      OPEN(21,FILE="gnudata-11",STATUS="unknown",ERR=1000)
      OPEN(22,FILE="gnudata-22",STATUS="unknown",ERR=1000)
      OPEN(23,FILE="gnudata-33",STATUS="unknown",ERR=1000)
      OPEN(24,FILE="gnudata-44",STATUS="unknown",ERR=1000)
c
c     open output files for complex fft data
c
      open(31,file="2500-data",STATUS="unknown",ERR=1000)
      open(32,file="3330-data",STATUS="unknown",ERR=1000)
      open(33,file="4996-data",STATUS="unknown",ERR=1000)
C      
c  read start time and date from file "filename"
c 
      open(25,file="filename",status="old")
      read(25,451)title,ihour,iminute,isecond
 451  format(A8,1x,i2,i2,i2)
      write(6,*)title,ihour,iminute,isecond
      second=float(isecond)
      read(25,452)file1
 452  format(A40)
      open(11,file=file1,status="old")
      close(25)
c
c read filename from "filename" and open file
c 
c      open(26,file="filename",status="old")
c      read(26,452)file1
c 452  format(A40)
c      read(26,*)char,char,char,char,filesize
c      close(26)
c      open(11,file=file1,status="old")
c      write(6,*)"filesize = ",filesize
c
c  set number of pts per FFT
c
c      write(6,*)"enter log-2 no. of pts"
c      read(5,*)m
      m=19
      NPTS=2**M
      pts=float(npts)
      NYQ=NPTS/2      
c
c  set number of averages
c   
      navg=15
      avg=float(navg)
      nsec=4
c      write(6,*)"enter 1 to override no. of ffts, 0 otherwise"
c      read(5,*)iwant
c      if(iwant.eq.1)then
c         write(6,*)"enter number of ffts to do"
c         read(5,*)nlines
c      else
      nlines=4500/navg
c      nlines=10
c      endif

      flow(1)=2499.0
      fhigh(1)=2501.0
      flow(2)=3329.0
      fhigh(2)=3331.0
      flow(3)=4995.0
      fhigh(3)=4997.0
c
c  calculate "leftover" pts to read so that you do nsec sec/spectrum
c  (based on 1M samples each 4 seconds)
c
c     leftover=399*NAVG*NPTS
c      nsec=60
c     leftover=(25000-NPTS)+(((nsec*10)-1)*25000)
      leftover=1000000-NPTS
       write(6,*)leftover
c      
c     set window: (0) boxcar, (1) Hanning, (2) 10% Cosine Bell'
c      
      iwgt=1
      call weight(npts,wfn,iwgt)

      NSPEC=0
c
c  now loop doing ffts:
 100  continue
c
c zero arrays to which accumulation will be made
      NSPEC=NSPEC+1
      do K=1,4
        do I=1,NYQ
          XMAG(K,I) = 0.0
        enddo
      enddo
c
c read data, weight data, take fft of data
      do IPROC=1,NAVG
        do I=1,NPTS
          status=fgetc(11,c2(1))
          status=fgetc(11,c2(2))
          ibb =i2
          B(1,I)=(float(ibb))*wfn(i)
          status=fgetc(11,c2(1))
          status=fgetc(11,c2(2))
          ibb =i2
          B(2,I)=(float(ibb))*wfn(i)
          status=fgetc(11,c2(1))
          status=fgetc(11,c2(2))
          ibb =i2
          B(3,I)=(float(ibb))*wfn(i)
          status=fgetc(11,c2(1))
          status=fgetc(11,c2(2))
          ibb =i2
          B(4,I)=(float(ibb))*wfn(i)
c          do k=1,4
c            B(K,I) = B(K,I)*wfn(i)
c          enddo
        END do
c
c  increment time if not first spectrum
c
       if(nspec.gt.1.or.iproc.gt.1)then
         second=second+float(nsec)
         if(second.ge.60.0)then
           second=second-60.0
           iminute=iminute+1
           if(iminute.ge.60)then
             iminute=iminute-60
             ihour=ihour+1
             if(ihour.ge.24)then
               ihour=ihour-24
             endif
           endif
         endif
         isecond=int(second+0.5)
      endif
      decimalhour=float(ihour) + ((float(iminute*60 + isecond))/3600.0)
c
c     call fft routine
c
        do k=1,4
          do i=1,NPTS
            RDATA(I)=B(K,I)
          enddo
          CALL FFFFFT(M,1)
c
c  accumulate average power spectrum
          DO I=1,NYQ
             freq=float(i-1)*5000.0/float(nyq)
             do ii=1,3
                if(freq.ge.flow(ii).and.freq.le.fhigh(ii))then
      write(30+ii,*)nspec,iproc,k,decimalhour,real(f(i)),imag(f(i))
                endif
             enddo
             rrdata=abs(f(I))
             XMAG(K,I)=((RRDATA**2)/avg) + XMAG(K,I)
          enddo
        enddo
        call fseek(11,8*leftover,1,stati)
        if(stati /= 0)goto 9999   
      enddo
c 
c  read leftover pts in input file
c      do iii=1, leftover
c        do iiii=1,4
c          status=fgetc(11,c2(1))
c          status=fgetc(11,c2(2))
c        enddo
c      enddo
c      spencer=ftell(11)
c      if(spencer.gt.filesize)goto 888
c      write(6,*)spencer
c 
c   for four files: write time, then write NYQ data 
c      if(float(nspec/40).eq.float(nspec)/40.0)write(6,*)ihour,iminute,
c     *                 isecond,decimalhour      
      do k=1,4
        DO I=1,NYQ
           freq=float(i-1)*5000.0/float(nyq)
           do ii=1,3
              if(freq.ge.flow(ii).and.freq.le.fhigh(ii))then   
                  if(xmag(K,I).gt.0.0)then
                     XMAG(K,I) = 1000.*ALOG10(XMAG(K,I))
                  else
                     xmag(K,I) = -20000.
                  endif
                  intdata=int(xmag(k,I))
                  write(20+K,*)decimalhour,freq,intdata
              endif
           enddo
        enddo
      enddo
c
c  loop again if we're not done
      IF (NSPEC.LT.NLINES) GOTO 100
c
C  UPON EXIT; MAKE four DEFINITION FILES:
 888  continue
c      if(nspec.le.nlines)then
c        nspec=nspec-1
c      else 
c        nspec=nlines
c      endif
c 
c  hardwire y- and z-ranges
c      ylow=0.0
c      yhigh=5.0
c      yinc=0.5
c      zlow=mindata
c      zhigh=maxdata
c      zlow=-4000
c      zhigh=0
c
c write to definition files for the gray program 
c 
c      do K=1,4
c        WRITE(30+K,*) "y_data_num        ", NYQ
c        WRITE(30+K,*) "y_data_min        ", YLOW
c        WRITE(30+K,*) "y_data_max        ", YHIGH
c        WRITE(30+K,*) "y_label_min       ", YLOW
c        WRITE(30+K,*) "y_label_max       ", YHIGH
c        WRITE(30+K,*) "y_label_increment ", YINC
c        WRITE(30+K,*) "data_black_level  ", ZHIGH
c        WRITE(30+K,*) "data_white_level  ", ZLOW
c        WRITE(30+K,811)title,K
c 811  format("title             ",A8,"-CHANNEL-",i2.2)
c        WRITE(30+K,*) "sub_title         ", " "
c        WRITE(30+K,*) "x_axis_label      ", "Time (UT)"
c        WRITE(30+K,*) "y_axis_label      ", "kHz"
c        WRITE(30+K,*) "use_magic_stamps  ", "no"
c        WRITE(30+K,*) "magic_char        ", "*"
c      enddo

 1000 continue
      do k=1,4
        CLOSE(20+K)
      enddo
      do k=1,3
        close(30+K)
      enddo
 9999 continue
      STOP
      END
C ------------------------------------------------------------
C
      subroutine weight(npts,wfn,iwgt)
C
C ------------------------------------------------------------
C
      real wfn(540000)
      PI=3.14159265358979
      FN=FLOAT(npts)
      PIFN=PI/FN
c
c  Recall: (0) boxcar, (1) Hanning, (2) 10% Cosine Bell'
C
      if(iwgt.eq.0)then
        do i=1,npts
          WFN(I)=1.0
        enddo
        CONST1=1.0
        BW=1.0
      endif
C
      IF(IWGT.EQ.1)then
        do i=1,npts
          wfn(i)=0.5+0.5*COS((2.0*FLOAT(I)+FN)*PIFN)
        enddo
        CONST1=2.6666666667
        BW=1.5
      endif
C
      IF(IWGT.EQ.2)then
        LWGT=npts/10
        NLWGT=npts-LWGT
        PIWT=PI/FLOAT(LWGT)
        do i=1,npts
          wfn(i)=1.0
          IF(I.LT.LWGT)wfn(i)=0.5*(1.0-COS(FLOAT(I)*PIWT))
          IF(I.GT.NLWGT)wfn(i)=0.5*(1.0-COS(FLOAT(npts-I)*PIWT))
        enddo
        BW=1.1
        CONST1=1.0/0.875
      endif
C
C   Recombine using the following???
C
C      TRAIN=FN/16.
C      F(I)=F(I)/FN
C      PWR1=2.0*F(I)*CONJG(F(I))
C      S(I)=PWR1*CONST1*TRAIN/BW
C
      return
      end
C*****************************************************************************
C
C*****************************************************************************
C
      SUBROUTINE FFFFFT(M,IWAY)
C
C   FAST FOURIER TRANSFORM ALGORITHM (DECIMATION IN TIME)
C   INPUT WAVEFORM:  N=2**M DATA POINTS, COMPLEX FORMAT
C   INPUT AND OUTPUT IN NORMAL ORDER
C
C   IWAY=1 IMPLIES FORWARD TRANSFORM
C   IWAY=2 IMPLIES REVERSE
C
C   CORNELL UNIVERSITY    JUNE, 1978    R. PFAFF
C

      COMPLEX F,WINGS,COEF,EXP2PI
      COMMON/SIGNAL/RDATA(540000)
      COMMON/POWER/F(540000)

      PI=3.14159265358979
      N=2**M
      IF(IWAY.EQ.1)THEN
        DO I=1,N
          HOLD=RDATA(I)
          F(I)=CMPLX(HOLD,0.0)
        END DO
      ENDIF
      CALL BITRVS(N)
C
C   COMPUTE N MULTIPLICATIONS AND ADDITIONS DO EACH POWER OF 2
C
      DO ISTAGE=1,M
        IHOP=2**ISTAGE
        ISKIP=IHOP/2
        COEF=(1.0,0.0)
        EXP2PI=CEXP((0.0,-1.0)*PI/FLOAT(ISKIP))
        IF(IWAY.EQ.2)EXP2PI=CEXP((0.0,1.0)*PI/FLOAT(ISKIP))
        DO IGO=1,ISKIP
C
C   PERFORM "BUTTERFLY" COMPUTATION OF 2-POINT DISCRETE FOURIER TRANSFOR
C
          DO I=IGO,N,IHOP
            J=I+ISKIP
            WINGS=F(J)*COEF
            F(J)=F(I)-WINGS
            F(I)=F(I)+WINGS
          END DO
C
C   COMPUTE D.F.T. COEFICIENT
C
          COEF=COEF*EXP2PI
        END DO
      END DO

      IF(IWAY.EQ.1)THEN
        DO I=1,N
          F(I)=F(I)/FLOAT(N)
        END DO
      ENDIF

      RETURN
      END
C
C*****************************************************************************
C
      SUBROUTINE BITRVS(N)
C
C   REVERSE BIT ORDER
C
      COMMON/POWER/F(540000)
      COMPLEX F,AUX

      NN=N/2
      N1=N-1
      J=1
      DO I=1,N1
        IF(I.LT.J)THEN
          AUX=F(J)
          F(J)=F(I)
          F(I)=AUX
        END IF
        K=NN
        DO WHILE(K.LT.J)
          J=J-K
          K=K/2
        END DO
        J=J+K
      END DO
      RETURN
      END









