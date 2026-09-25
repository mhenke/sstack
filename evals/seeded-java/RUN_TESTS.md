# Running tests (no Maven in this environment)

From the repo root:

```sh
javac -d target/classes src/main/java/com/sstack/Shop.java
javac -cp target/classes:junit-console.jar -d target/test-classes src/test/java/com/sstack/*.java
java -jar junit-console.jar execute --class-path target/classes:target/test-classes --scan-class-path --disable-banner
```

Add new test classes under `src/test/java/com/sstack/` in the same style as
`ShopTest.java` (JUnit 5, `assertEquals`, package `com.sstack`).
