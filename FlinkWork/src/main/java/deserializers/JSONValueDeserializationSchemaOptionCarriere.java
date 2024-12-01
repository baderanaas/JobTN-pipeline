package deserializers;

import DTO.OptionCarriere;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.serialization.DeserializationSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;

import java.io.IOException;

public class JSONValueDeserializationSchemaOptionCarriere implements DeserializationSchema<OptionCarriere> {

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Override
    public void open(InitializationContext context) throws Exception {
        DeserializationSchema.super.open(context);
    }

    @Override
    public OptionCarriere deserialize(byte[] bytes) throws IOException {
        return objectMapper.readValue(bytes, OptionCarriere.class);
    }

    @Override
    public boolean isEndOfStream(OptionCarriere OptionCarriere) {
        return false;
    }

    @Override
    public TypeInformation<OptionCarriere> getProducedType() {
        return TypeInformation.of(OptionCarriere.class);
    }
}

