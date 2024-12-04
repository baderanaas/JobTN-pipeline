package DTO;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.sql.Timestamp;

@Data
public class Jobs {
    private String link;
    @JsonProperty("Company")
    private String company;
    private Timestamp expiration_date;
    @JsonProperty("Title")
    private String title;
    @JsonProperty("Description")
    private String description;
    @JsonProperty("Workplace")
    private String workplace;
}
