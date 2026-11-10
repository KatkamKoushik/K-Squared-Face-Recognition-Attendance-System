plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.kucet.frs.frs_teacher_app"
    compileSdk = 35
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
        minSdk = 21 // Android 5.0 (API 21) resolves package conflicts with image_picker and AndroidX
        targetSdk = 35 // Android 15 & 16 target compatibility
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    signingConfigs {
        create("release") {
            val keystorePath = System.getenv("KEYSTORE_PATH") ?: project.findProperty("KEYSTORE_PATH") as String?
            val candidatePaths = listOfNotNull(
                keystorePath?.let { file(it) },
                keystorePath?.let { file("../$it") },
                keystorePath?.let { file("../../$it") },
                keystorePath?.let { rootProject.file("../$it") },
                file("ci-release-keystore.jks"),
                file("upload-keystore.jks"),
                file("../upload-keystore.jks"),
                file("../../upload-keystore.jks")
            )
            val targetFile = candidatePaths.firstOrNull { it.exists() }

            if (targetFile != null && targetFile.exists()) {
                storeFile = targetFile
                storePassword = System.getenv("KEYSTORE_PASSWORD") ?: project.findProperty("KEYSTORE_PASSWORD") as String? ?: "android"
                keyAlias = System.getenv("KEY_ALIAS") ?: project.findProperty("KEY_ALIAS") as String? ?: "k2-ci-release"
                keyPassword = System.getenv("KEY_PASSWORD") ?: project.findProperty("KEY_PASSWORD") as String? ?: "android"
            } else {
                // When building in environments without provisioned release keystore,
                // fall back to the default debug signing configuration so APK generation succeeds.
                val debugConfig = signingConfigs.getByName("debug")
                storeFile = debugConfig.storeFile
                storePassword = debugConfig.storePassword
                keyAlias = debugConfig.keyAlias
                keyPassword = debugConfig.keyPassword
            }
        }
    }

    buildTypes {
        debug {
            signingConfig = signingConfigs.getByName("debug")
        }
        release {
            signingConfig = signingConfigs.getByName("release")
        }
    }
}

flutter {
    source = "../.."
}
