allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

subprojects {
    afterEvaluate {
        val extension = project.extensions.findByName("android")
        if (extension != null) {
            try {
                val setter = extension.javaClass.getMethod("setCompileSdkVersion", Int::class.java)
                setter.invoke(extension, 36)
            } catch (e: Exception) {
                try {
                    val property = extension.javaClass.getMethod("setCompileSdk", Int::class.java)
                    property.invoke(extension, 36)
                } catch (ignored: Exception) {}
            }
        }
    }
}

subprojects {
    tasks.matching { it.name.contains("lintVital") || it.name.contains("Lint") }.configureEach {
        enabled = false
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
