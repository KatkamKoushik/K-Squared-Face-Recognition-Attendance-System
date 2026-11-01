import 'package:flutter/material.dart';

/// FRS V7.1 K2 Design System: Swiss Modernism 2.0 (Academic Precision)
/// Follows Material 3, strict contrast (>= 4.5:1), and zero AI-slop gradients.
/// Fully offline-first without dynamic network font downloads.
class AppTheme {
  // Institutional Palette
  static const Color primaryNavy = Color(0xFF1E3A5F);
  static const Color secondaryBlue = Color(0xFF0284C7);
  static const Color accentGold = Color(0xFFA16207);
  static const Color surfaceLight = Color(0xFFFFFFFF);
  static const Color backgroundLight = Color(0xFFF8FAFC);
  static const Color surfaceVariantLight = Color(0xFFF1F5F9);
  static const Color borderLight = Color(0xFFCBD5E1);
  static const Color textMainLight = Color(0xFF0F172A);
  static const Color textMutedLight = Color(0xFF475569);
  static const Color errorRed = Color(0xFFDC2626);

  // Evidence Status Colors
  static const Color statusMatched = Color(0xFF16A34A); // Proposed Present
  static const Color statusReview = Color(0xFFD97706); // Human Review
  static const Color statusRecapture = Color(0xFFEA580C); // Recapture Required
  static const Color statusUnknown = Color(0xFF64748B); // Unrecognized
  static const Color statusError = Color(0xFFDC2626); // Pipeline Error
  static const Color statusManual = Color(0xFF7C3AED); // Manual Exception
  static const Color statusCommitted = Color(0xFF0D9488); // Finalized Ledger

  static ThemeData get lightTheme {
    final baseColorScheme = ColorScheme(
      brightness: Brightness.light,
      primary: primaryNavy,
      onPrimary: Colors.white,
      secondary: secondaryBlue,
      onSecondary: Colors.white,
      error: errorRed,
      onError: Colors.white,
      surface: surfaceLight,
      onSurface: textMainLight,
      surfaceContainerHighest: surfaceVariantLight,
      outline: borderLight,
    );

    return ThemeData(
      useMaterial3: true,
      colorScheme: baseColorScheme,
      scaffoldBackgroundColor: backgroundLight,
      fontFamily: 'Roboto',
      textTheme: const TextTheme(
        displayLarge: TextStyle(
          fontSize: 32,
          fontWeight: FontWeight.bold,
          color: textMainLight,
          height: 1.25,
          fontFamily: 'serif',
        ),
        headlineMedium: TextStyle(
          fontSize: 24,
          fontWeight: FontWeight.w600,
          color: textMainLight,
          height: 1.3,
          fontFamily: 'serif',
        ),
        titleLarge: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w600,
          color: textMainLight,
          height: 1.35,
        ),
        bodyLarge: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w400,
          color: textMainLight,
          height: 1.5,
        ),
        bodyMedium: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w400,
          color: textMutedLight,
          height: 1.5,
        ),
        labelLarge: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.2,
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryNavy,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w600,
          color: Colors.white,
          fontFamily: 'serif',
        ),
      ),
      cardTheme: CardThemeData(
        color: surfaceLight,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: const BorderSide(color: borderLight, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryNavy,
          foregroundColor: Colors.white,
          minimumSize: const Size(88, 48), // >= 44dp touch target
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: primaryNavy,
          minimumSize: const Size(88, 48),
          side: const BorderSide(color: borderLight, width: 1.5),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceLight,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: primaryNavy, width: 2),
        ),
        labelStyle: const TextStyle(color: textMutedLight),
      ),
    );
  }
}
