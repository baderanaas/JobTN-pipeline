package FlinkWork;

import DTO.*;
import deserializers.*;

import org.apache.flink.api.common.restartstrategy.RestartStrategies;
import org.apache.flink.api.common.time.Time;
import org.apache.flink.connector.jdbc.JdbcConnectionOptions;
import org.apache.flink.connector.jdbc.JdbcExecutionOptions;
import org.apache.flink.connector.jdbc.JdbcStatementBuilder;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.connector.jdbc.JdbcSink;

import java.util.concurrent.TimeUnit;


public class DataStreamJob {
	private static final String jdbcUrl = "jdbc:postgresql://localhost:6543/jobs";
	private static final String username = "postgres";
	private static final String password = "postgres";

	public static void main(String[] args) throws Exception {
		System.setProperty("log4j2.debug", "true");
		final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

		KafkaSource<Farojob> sourceFarojob = KafkaSource.<Farojob>builder()
				.setBootstrapServers("localhost:9092")
				.setTopics("farojob")
				.setGroupId("job-group")
				.setStartingOffsets(OffsetsInitializer.earliest())
				.setValueOnlyDeserializer(new JSONValueDeserializationSchemaFarojob())
				.build();

		DataStream<Farojob> streamFarojob = env.fromSource(sourceFarojob, WatermarkStrategy.noWatermarks(), "Kafka Farojob Source");

		streamFarojob.print();

		KafkaSource<Keejob> sourceKeejob = KafkaSource.<Keejob>builder()
				.setBootstrapServers("localhost:9092")
				.setTopics("keejob")
				.setGroupId("job-group")
				.setStartingOffsets(OffsetsInitializer.earliest())
				.setValueOnlyDeserializer(new JSONValueDeserializationSchemaKeejob())
				.build();

		DataStream<Keejob> streamKeejob = env.fromSource(sourceKeejob, WatermarkStrategy.noWatermarks(), "Kafka Keejob Source");

		// streamKeejob.print();

		KafkaSource<Hi_interns> sourceHi_interns = KafkaSource.<Hi_interns>builder()
				.setBootstrapServers("localhost:9092")
				.setTopics("hi_interns")
				.setGroupId("job-group")
				.setStartingOffsets(OffsetsInitializer.earliest())
				.setValueOnlyDeserializer(new JSONValueDeserializationSchemaHiInterns())
				.build();

		DataStream<Hi_interns> streamHi_interns = env.fromSource(sourceHi_interns, WatermarkStrategy.noWatermarks(), "Kafka Hi_interns Source");

		// streamHi_interns.print();

		KafkaSource<OptionCarriere> sourceOptionCarriere = KafkaSource.<OptionCarriere>builder()
				.setBootstrapServers("localhost:9092")
				.setTopics("option_carriere")
				.setGroupId("job-group")
				.setStartingOffsets(OffsetsInitializer.earliest())
				.setValueOnlyDeserializer(new JSONValueDeserializationSchemaOptionCarriere())
				.build();

		DataStream<OptionCarriere> streamOptionCarriere = env.fromSource(
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
						"body TEXT" +
						")",
				(JdbcStatementBuilder<Keejob>) (preparedStatement, keejob) -> {

				},
				execOptions,
				connOptions
		)).name("Create Keejob Table Sink");

		streamKeejob.addSink(JdbcSink.sink(
				"INSERT INTO keejob (link, body) " +
						"VALUES (?, ?) " +
						"ON CONFLICT (link) DO UPDATE SET " +
						"body = EXCLUDED.body",
				(JdbcStatementBuilder<Keejob>) (preparedStatement, keejob) -> {
					preparedStatement.setString(1, keejob.getLink());
					preparedStatement.setString(2, keejob.getBody());
				},
				execOptions,
				connOptions
		)).name("Insert into Keejob table sink");

		streamOptionCarriere.addSink(JdbcSink.sink(
				"CREATE TABLE IF NOT EXISTS option_carriere (" +
						"link TEXT PRIMARY KEY, " +
						"body TEXT" +
						")",
				(JdbcStatementBuilder<OptionCarriere>) (preparedStatement, optionCarriere) -> {
				},
				execOptions,
				connOptions
		)).name("Create OptionCarriere Table Sink");

		streamOptionCarriere.addSink(JdbcSink.sink(
				"INSERT INTO option_carriere (link, body) " +
						"VALUES (?, ?) " +
						"ON CONFLICT (link) DO UPDATE SET " +
						"body = EXCLUDED.body",
				(JdbcStatementBuilder<OptionCarriere>) (preparedStatement, optionCarriere) -> {
					preparedStatement.setString(1, optionCarriere.getLink());
					preparedStatement.setString(2, optionCarriere.getBody());
				},
				execOptions,
				connOptions
		)).name("Insert into OptionCarriere table sink");

		streamFarojob.addSink(JdbcSink.sink(
				"CREATE TABLE IF NOT EXISTS farojob (" +
						"link TEXT PRIMARY KEY, " +
						"body TEXT," +
						"date TIMESTAMP"+
						")",
				(JdbcStatementBuilder<Farojob>) (preparedStatement, farojob) -> {
				},
				execOptions,
				connOptions
		)).name("Create Farojob Table Sink");

		streamFarojob.addSink(JdbcSink.sink(
				"INSERT INTO farojob (link, body, date) " +
						"VALUES (?, ?, ?) " +
						"ON CONFLICT (link) DO UPDATE SET " +
						"body = EXCLUDED.body," +
						"date = EXCLUDED.date"
				,
				(JdbcStatementBuilder<Farojob>) (preparedStatement, farojob) -> {
					preparedStatement.setString(1, farojob.getLink());
					preparedStatement.setString(2, farojob.getBody());
					preparedStatement.setString(3, farojob.getDate());
				},
				execOptions,
				connOptions
		)).name("Insert into Farojob table sink");

		streamHi_interns.addSink(JdbcSink.sink(
				"CREATE TABLE IF NOT EXISTS hi_interns (" +
						"link TEXT PRIMARY KEY, " +
						"body TEXT" +
						")",
				(JdbcStatementBuilder<Hi_interns>) (preparedStatement, hiInterns) -> {
				},
				execOptions,
				connOptions
		)).name("Create Hi_interns Table Sink");

		streamHi_interns.addSink(JdbcSink.sink(
				"INSERT INTO hi_interns (link, body) " +
						"VALUES (?, ?) " +
						"ON CONFLICT (link) DO UPDATE SET " +
						"body = EXCLUDED.body",
				(JdbcStatementBuilder<Hi_interns>) (preparedStatement, hiInterns) -> {
					preparedStatement.setString(1, hiInterns.getLink());
					preparedStatement.setString(2, hiInterns.getBody());
				},
				execOptions,
				connOptions
		)).name("Insert into Hi_interns table sink");
		env.setRestartStrategy(RestartStrategies.fixedDelayRestart(3, Time.of(10, TimeUnit.SECONDS)));
		env.execute("Flink Job Processing and Database Integration");
	}
}
