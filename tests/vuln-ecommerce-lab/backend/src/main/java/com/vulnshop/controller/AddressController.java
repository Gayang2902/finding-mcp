package com.vulnshop.controller;

import com.vulnshop.dto.request.AddressRequest;
import com.vulnshop.dto.response.AddressResponse;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.AddressService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/addresses")
public class AddressController {

    private final AddressService addressService;

    public AddressController(AddressService addressService) {
        this.addressService = addressService;
    }

    @PostMapping("/")
    public ResponseEntity<AddressResponse> addAddress(@Valid @RequestBody AddressRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(addressService.addAddress(currentUserId, request));
    }

    // VULN: IDOR - no ownership check, any user can update any address by ID
    @PutMapping("/{id}")
    public ResponseEntity<AddressResponse> updateAddress(@PathVariable Long id,
                                                          @Valid @RequestBody AddressRequest request) {
        return ResponseEntity.ok(addressService.updateAddress(id, request));
    }

    // VULN: IDOR - no ownership check, any user can delete any address by ID
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteAddress(@PathVariable Long id) {
        addressService.deleteAddress(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/")
    public ResponseEntity<List<AddressResponse>> getUserAddresses() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(addressService.getUserAddresses(currentUserId));
    }

    // VULN: IDOR - no ownership check, any user can view any address by ID
    @GetMapping("/{id}")
    public ResponseEntity<AddressResponse> getAddressById(@PathVariable Long id) {
        return ResponseEntity.ok(addressService.getAddressById(id));
    }

    @PutMapping("/{id}/default")
    public ResponseEntity<AddressResponse> setDefaultAddress(@PathVariable Long id) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(addressService.setDefaultAddress(currentUserId, id));
    }
}
