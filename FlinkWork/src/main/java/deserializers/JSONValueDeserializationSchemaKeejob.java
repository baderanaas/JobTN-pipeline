package deserializers;

import DTO.Keejob;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class JSONValueDeserializationSchemaKeejob implements DeserializationSchema<Keejob> {

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public Keejob deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, Keejob.class);
    }

    @Override
    public boolean isEndOfStream(Keejob keejob) {
        return false;
    }

    @Override
    public TypeInformation<Keejob> getProducedType() {
        return TypeInformation.of(Keejob.class);
    }
}
