plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.kucet.frs.frs_teacher_app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    defaultConfig {
        applicationId = "com.kucet.frs.frs_teacher_app"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        create("release") {
            val keystorePath = System.getenv("KEYSTORE_PATH") ?: project.findProperty("KEYSTORE_PATH") as String?
            val targetFile = if (keystorePath != null) {
                val f = file(keystorePath)
                if (f.exists()) f else file("../$keystorePath")
            } else null

            if (targetFile != null && targetFile.exists()) {
                storeFile = targetFile
                storePassword = System.getenv("KEYSTORE_PASSWORD") ?: project.findProperty("KEYSTORE_PASSWORD") as String? ?: ""
                keyAlias = System.getenv("KEY_ALIAS") ?: project.findProperty("KEY_ALIAS") as String? ?: ""
                keyPassword = System.getenv("KEY_PASSWORD") ?: project.findProperty("KEY_PASSWORD") as String? ?: ""
            } else {
                // In CI / dev when no custom keystore is provided, generate or use debug keystore
                val debugKeystore = file("${System.getProperty("user.home")}/.android/debug.keystore")
                if (!debugKeystore.exists()) {
                    debugKeystore.parentFile?.mkdirs()
                    val keytool = "${System.getProperty("java.home")}/bin/keytool"
                    ProcessBuilder(
                        keytool, "-genkey", "-v",
                        "-keystore", debugKeystore.absolutePath,
                        "-alias", "androiddebugkey",
                        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                        "-storepass", "android", "-keypass", "android",
                        "-dname", "CN=Android Debug,O=Android,C=US"
                    ).inheritIO().start().waitFor()
                }
                storeFile = debugKeystore
                storePassword = "android"
                keyAlias = "androiddebugkey"
                keyPassword = "android"
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

flutter {
    source = "../.."
}
