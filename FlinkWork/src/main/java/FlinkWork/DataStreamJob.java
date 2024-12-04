package FlinkWork;

import DTO.Jobs;
import deserializers.JSONValueDeserializationSchema;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.restartstrategy.RestartStrategies;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.connector.jdbc.JdbcConnectionOptions;
import org.apache.flink.connector.jdbc.JdbcExecutionOptions;
import org.apache.flink.connector.jdbc.JdbcSink;
import org.apache.flink.connector.jdbc.JdbcStatementBuilder;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;

import java.util.concurrent.TimeUnit;


public class DataStreamJob {
    private static final String jdbcUrl = "jdbc:postgresql://localhost:6543/jobs";
    private static final String username = "postgres";
    private static final String password = "postgres";

    public static void main(String[] args) throws Exception {
        System.setProperty("log4j2.Debug", "true");
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        KafkaSource<Jobs> sourceFarojob = KafkaSource.<Jobs>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("farojob")
                .setGroupId("job-group")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new JSONValueDeserializationSchema())
                .build();

        DataStream<Jobs> streamFarojob = env.fromSource(sourceFarojob, WatermarkStrategy.noWatermarks(), "Kafka Farojob Source");

        streamFarojob.print();

        KafkaSource<Jobs> sourceKeejob = KafkaSource.<Jobs>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("keejob")
                .setGroupId("job-group")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new JSONValueDeserializationSchema())
                .build();

        DataStream<Jobs> streamKeejob = env.fromSource(sourceKeejob, WatermarkStrategy.noWatermarks(), "Kafka Keejob Source");

        // streamKeejob.print();

        KafkaSource<Jobs> sourceHi_interns = KafkaSource.<Jobs>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("hi_interns")
                .setGroupId("job-group")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new JSONValueDeserializationSchema())
                .build();

        DataStream<Jobs> streamHi_interns = env.fromSource(sourceHi_interns, WatermarkStrategy.noWatermarks(), "Kafka Hi_interns Source");

        // streamHi_interns.print();

        KafkaSource<Jobs> sourceOptionCarriere = KafkaSource.<Jobs>builder()
                .setBootstrapServers("localhost:9092")
                .setTopics("option_carriere")
                .setGroupId("job-group")
                .setStartingOffsets(OffsetsInitializer.earliest())
                .setValueOnlyDeserializer(new JSONValueDeserializationSchema())
                .build();

        DataStream<Jobs> streamOptionCarriere = env.fromSource(
                sourceOptionCarriere,
                WatermarkStrategy.noWatermarks(),
                "Kafka OptionCarriere Source"
        );

        // streamOptionCarriere.print();


        JdbcExecutionOptions execOptions = new JdbcExecutionOptions.Builder()
                .withBatchSize(1000)
                .withBatchIntervalMs(200)
                .withMaxRetries(5)
                .build();

        JdbcConnectionOptions connOptions = new JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                .withUrl(jdbcUrl)
                .withDriverName("org.postgresql.Driver")
                .withUsername(username)
                .withPassword(password)
                .build();

        streamKeejob.addSink(JdbcSink.sink(
                "CREATE TABLE IF NOT EXISTS keejob (" +
                        "link TEXT PRIMARY KEY, " +
                        "description TEXT, " +
                        "title TEXT, " +
                        "company TEXT, " +
                        "workplace TEXT, " +
                        "expiration_date TIMESTAMP" +
                        ")",
                (JdbcStatementBuilder<Jobs>) (preparedStatement, keejob) -> {

                },
                execOptions,
                connOptions
        )).name("Create Keejob Table Sink");

        streamKeejob.addSink(JdbcSink.sink(
                "INSERT INTO keejob (link, description, title, company, workplace, expiration_date) " +
                        "VALUES (?, ?, ?, ?, ?, ?) " +
                        "ON CONFLICT (link) DO UPDATE SET " +
                        "description = EXCLUDED.Description, " +
                        "title = EXCLUDED.title, " +
                        "company = EXCLUDED.company, " +
                        "workplace = EXCLUDED.workplace, " +
                        "expiration_date = EXCLUDED.expiration_date"
                ,
                (JdbcStatementBuilder<Jobs>) (preparedStatement, keejob) -> {
                    preparedStatement.setString(1, keejob.getLink());
                    preparedStatement.setString(2, keejob.getDescription());
                    preparedStatement.setString(3, keejob.getTitle());
                    preparedStatement.setString(4, keejob.getCompany());
                    preparedStatement.setString(5, keejob.getWorkplace());
                    preparedStatement.setTimestamp(6, keejob.getExpiration_date());
                },
                execOptions,
                connOptions
        )).name("Insert into Keejob table sink");

        streamOptionCarriere.addSink(JdbcSink.sink(
                "CREATE TABLE IF NOT EXISTS option_carriere (" +
                        "link TEXT PRIMARY KEY, " +
                        "description TEXT, " +
                        "title TEXT, " +
                        "company TEXT, " +
                        "workplace TEXT, " +
                        "expiration_date TIMESTAMP" +
                        ")",
                (JdbcStatementBuilder<Jobs>) (preparedStatement, optionCarriere) -> {
                },
                execOptions,
                connOptions
        )).name("Create OptionCarriere Table Sink");

        streamOptionCarriere.addSink(JdbcSink.sink(
                "INSERT INTO option_carriere (link, description, title, company, workplace, expiration_date) " +
                        "VALUES (?, ?, ?, ?, ?, ?) " +
                        "ON CONFLICT (link) DO UPDATE SET " +
                        "description = EXCLUDED.Description, " +
                        "title = EXCLUDED.Title, " +
                        "company = EXCLUDED.company, " +
                        "workplace = EXCLUDED.Workplace, " +
                        "expiration_date = EXCLUDED.expiration_date"
                ,
                (JdbcStatementBuilder<Jobs>) (preparedStatement, optionCarriere) -> {
                    preparedStatement.setString(1, optionCarriere.getLink());
                    preparedStatement.setString(2, optionCarriere.getDescription());
                    preparedStatement.setString(3, optionCarriere.getTitle());
                    preparedStatement.setString(4, optionCarriere.getCompany());
                    preparedStatement.setString(5, optionCarriere.getWorkplace());
                    preparedStatement.setTimestamp(6, optionCarriere.getExpiration_date());
                },
                execOptions,
                connOptions
        )).name("Insert into OptionCarriere table sink");

        streamFarojob.addSink(JdbcSink.sink(
                "CREATE TABLE IF NOT EXISTS farojob (" +
                        "link TEXT PRIMARY KEY, " +
                        "description TEXT, " +
                        "title TEXT, " +
                        "company TEXT, " +
                        "workplace TEXT, " +
                        "expiration_date TIMESTAMP" +
                        ")",
                (JdbcStatementBuilder<Jobs>) (preparedStatement, farojob) -> {
                },
                execOptions,
                connOptions
        )).name("Create Farojob Table Sink");

        streamFarojob.addSink(JdbcSink.sink(
                "INSERT INTO farojob (link, description, title, company, workplace, expiration_date) " +
                        "VALUES (?, ?, ?, ?, ?, ?) " +
                        "ON CONFLICT (link) DO UPDATE SET " +
                        "description = EXCLUDED.Description, " +
                        "title = EXCLUDED.title, " +
                        "company = EXCLUDED.company, " +
                        "workplace = EXCLUDED.workplace, " +
                        "expiration_date = EXCLUDED.expiration_date"
                ,
                (JdbcStatementBuilder<Jobs>) (preparedStatement, farojob) -> {
                    preparedStatement.setString(1, farojob.getLink());
                    preparedStatement.setString(2, farojob.getDescription());
                    preparedStatement.setString(3, farojob.getTitle());
                    preparedStatement.setString(4, farojob.getCompany());
                    preparedStatement.setString(5, farojob.getWorkplace());
                    preparedStatement.setTimestamp(6, farojob.getExpiration_date());
                },
                execOptions,
                connOptions
        )).name("Insert into Farojob table sink");

        streamHi_interns.addSink(JdbcSink.sink(
                "CREATE TABLE IF NOT EXISTS hi_interns (" +
                        "link TEXT PRIMARY KEY, " +
                        "description TEXT, " +
                        "title TEXT, " +
                        "company TEXT, " +
                        "workplace TEXT, " +
                        "expiration_date TIMESTAMP" +
                        ")",
                (JdbcStatementBuilder<Jobs>) (preparedStatement, hiInterns) -> {
                },
                execOptions,
                connOptions
        )).name("Create Hi interns Table Sink");

        streamHi_interns.addSink(JdbcSink.sink(
                "INSERT INTO hi_interns (link, description, title, company, workplace, expiration_date) " +
                        "VALUES (?, ?, ?, ?, ?, ?) " +
                        "ON CONFLICT (link) DO UPDATE SET " +
                        "description = EXCLUDED.Description, " +
                        "title = EXCLUDED.title, " +
                        "company = EXCLUDED.company, " +
                        "workplace = EXCLUDED.workplace, " +
                        "expiration_date = EXCLUDED.expiration_date"
                ,
                (JdbcStatementBuilder<Jobs>) (preparedStatement, hi_interns) -> {
                    preparedStatement.setString(1, hi_interns.getLink());
                    preparedStatement.setString(2, hi_interns.getDescription());
                    preparedStatement.setString(3, hi_interns.getTitle());
                    preparedStatement.setString(4, hi_interns.getCompany());
                    preparedStatement.setString(5, hi_interns.getWorkplace());
                    preparedStatement.setTimestamp(6, hi_interns.getExpiration_date());
                },
                execOptions,
                connOptions
        )).name("Insert into Hi interns table sink");
        env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, Time.of(10, TimeUnit.SECONDS)));
        env.execute("Flink Job Processing and Database Integration");
    }
}
