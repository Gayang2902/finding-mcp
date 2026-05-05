package com.vulnshop.controller;

import com.vulnshop.dto.request.LoginRequest;
import com.vulnshop.dto.request.RegisterRequest;
import com.vulnshop.dto.response.AuthResponse;
import com.vulnshop.dto.response.UserResponse;
import com.vulnshop.entity.User;
import com.vulnshop.security.JwtTokenProvider;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final UserService userService;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthController(UserService userService, PasswordEncoder passwordEncoder, JwtTokenProvider jwtTokenProvider) {
        this.userService = userService;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        // register() returns UserResponse
        UserResponse userResponse = userService.register(request);
        String token = jwtTokenProvider.generateToken(userResponse.getEmail(), userResponse.getRole().name());
        AuthResponse response = AuthResponse.builder()
                .token(token)
                .tokenType("Bearer")
                .expiresIn(86400000L)
                .user(userResponse)
                .build();
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        User user = userService.findByEmail(request.getEmail());
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
        String token = jwtTokenProvider.generateToken(user.getEmail(), user.getRole().name());
        UserResponse userResponse = userService.mapToResponse(user);
        AuthResponse response = AuthResponse.builder()
                .token(token)
                .tokenType("Bearer")
                .expiresIn(86400000L)
                .user(userResponse)
                .build();
        return ResponseEntity.ok(response);
    }

    @GetMapping("/me")
    public ResponseEntity<UserResponse> me() {
        Long userId = SecurityUtils.getCurrentUserId();
        // findById returns User entity; map to response
        User user = userService.findById(userId);
        return ResponseEntity.ok(userService.mapToResponse(user));
    }
}
