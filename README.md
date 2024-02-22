# NullPointers-In-Andorid
bugs in android that cause a dos. 

I was needing a break form IOS and MACos so I deviced to focous on Android  bugs and a way to find them, this lead me down a rabit hole about service calls. In this write up, I will cover service calls, and a null defefferecne which leads to the device shutting off once sent via abd to the device. 

https://source.android.com/static/images/android-stack.svg 

We can se that the services are on a good level and can possibly deliver some bugs if we fuzz them, the idea was spawned from this write up on obtaining lpe on Andorid but the code provided was vauge, so I wrote the service fuzzer, the research took around 40/50 hours to do, as there was a lot of trial andf error. 






covering the crash, afetr we send our service call, to the wifi stack, we can see the following crash, if we continie to spam the device with the packets after the null pointer it then shuts off the device and causes a reboot, for some reason I do not know why. But this is what it does. 

```bash 
02-16 19:26:51.886  2203  3328 E AndroidRuntime: *** FATAL EXCEPTION IN SYSTEM PROCESS: WifiHandlerThread
02-16 19:26:51.886  2203  3328 E AndroidRuntime: java.lang.NullPointerException: Attempt to read from field 'java.util.HashMap android.net.wifi.WifiEnterpriseConfig.mFields' on a null object reference in method 'void android.net.wifi.WifiEnterpriseConfig.copyFrom(android.net.wifi.WifiEnterpriseConfig, boolean, java.lang.String)
```
Now if the Javascript code is then reviewed this can be traced to the following paramaters of the JS object. 

https://source.android.com/static/docs/core/architecture/images/wifi-components.png
##  WifiEnterpriseConfig.copyFrom(android.net.wifi.WifiEnterpriseConfig, boolean, java.lang.String)

The following function requires three main paramaters, these consist of

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


https://issuetracker.google.com/issues/326278126
