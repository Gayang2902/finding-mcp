package com.vulnshop.dto.request;

import com.vulnshop.entity.AddressLabel;
import jakarta.validation.constraints.NotBlank;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AddressRequest {

    private AddressLabel label;

    @NotBlank(message = "Full name is required")
    private String fullName;

    @NotBlank(message = "Street address is required")
    private String streetAddress;

    private String streetAddress2;

    @NotBlank(message = "City is required")
    private String city;

    @NotBlank(message = "State is required")
    private String state;

    @NotBlank(message = "Zip code is required")
    private String zipCode;

    @NotBlank(message = "Country is required")
    private String country;

    private String phone;

    private boolean isDefault;
}
