package deserializers;

import DTO.Jobs;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class JSONValueDeserializationSchema implements DeserializationSchema<Jobs> {
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public Jobs deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, Jobs.class);
    }

    @Override
    public boolean isEndOfStream(Jobs jobs) {
        return false;
    }

    @Override
    public TypeInformation<Jobs> getProducedType() {
        return TypeInformation.of(Jobs.class);
    }
}