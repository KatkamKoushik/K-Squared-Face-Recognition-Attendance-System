/// Official KUCET Academic Coordinators and Faculty Directory.
/// Extracted from official institutional registers of KU College of Engineering & Technology.
class FacultyCoordinator {
  final String name;
  final String designation;
  final String department;
  final String? mobileNumber;
  final String? emailId;
  final String category;
  final List<String> additionalRoles;

  const FacultyCoordinator({
    required this.name,
    required this.designation,
    required this.department,
    this.mobileNumber,
    this.emailId,
    required this.category,
    this.additionalRoles = const [],
  });
}

class KucetFacultyDirectory {
  static const List<FacultyCoordinator> academicCoordinators = [
    FacultyCoordinator(
      name: 'Dr. M. Soujanya',
      designation: 'Assistant Professor (c)',
      department: 'IT',
      mobileNumber: '9010610430',
      emailId: 'soujanyavedh@gmail.com',
      category: 'Academic Coordinator',
      additionalRoles: ['Alumni Affairs (IT & CSD)', 'NSS Program Officer (IT)'],
    ),
    FacultyCoordinator(
      name: 'Mr. V. Ramana Babu',
      designation: 'Assistant Professor (c)',
      department: 'CSE',
      mobileNumber: '9346313635',
      emailId: 'ramana.vrb@gmail.com',
      category: 'Academic Coordinator',
      additionalRoles: ['Director - Placements', 'Coordinator CSE/IT/CSD'],
    ),
    FacultyCoordinator(
      name: 'Mrs. B. Srilatha',
      designation: 'Assistant Professor (c)',
      department: 'ECE',
      category: 'Academic Coordinator',
    ),
    FacultyCoordinator(
      name: 'Dr. A. Kumara Swamy',
      designation: 'Assistant Professor (c)',
      department: 'EEE',
      category: 'Academic Coordinator',
    ),
    FacultyCoordinator(
      name: 'Dr. Md. Owais Ahmed Sajjad',
      designation: 'Assistant Professor (c)',
      department: 'MEC',
      mobileNumber: '9908716004',
      emailId: 'sajjad.owais44@gmail.com',
      category: 'Academic Coordinator',
    ),
    FacultyCoordinator(
      name: 'Mrs. D. Priyanka',
      designation: 'Assistant Professor (c)',
      department: 'CSD',
      mobileNumber: '8106061311',
      emailId: 'priyankadamera1223@gmail.com',
      category: 'Academic Coordinator',
      additionalRoles: ['Extra Curricular Activities CSD'],
    ),
    FacultyCoordinator(
      name: 'Mr. V. Amarender',
      designation: 'Assistant Professor (c)',
      department: 'CIVIL',
      category: 'Academic Coordinator',
    ),
  ];

  static const List<FacultyCoordinator> mTechCoordinators = [
    FacultyCoordinator(
      name: 'Mrs. V. Rajasree',
      designation: 'Assistant Professor (c)',
      department: 'DC',
      mobileNumber: '9963311463',
      emailId: 'rajasree.mitta@gmail.com',
      category: 'M.Tech Coordinator',
    ),
    FacultyCoordinator(
      name: 'Dr. M. Vani',
      designation: 'Assistant Professor (c)',
      department: 'CSE',
      mobileNumber: '8919611798',
      emailId: 'makula.vani@gmail.com',
      category: 'M.Tech Coordinator',
    ),
    FacultyCoordinator(
      name: 'Mrs. P. Rukmini',
      designation: 'Assistant Professor (c)',
      department: 'CAD/CAM',
      mobileNumber: '8897885118',
      emailId: 'rukmini.kucet@gmail.com',
      category: 'M.Tech Coordinator',
    ),
  ];

  static const List<FacultyCoordinator> placementOfficers = [
    FacultyCoordinator(
      name: 'Mr. V. Ramana Babu',
      designation: 'Director - Placements',
      department: 'CSE',
      mobileNumber: '9133612366',
      emailId: 'ramana.vrb@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Mr. Pakala Santhosh Kumar',
      designation: 'Training & Placement Officer',
      department: 'ECE',
      mobileNumber: '7396586731',
      emailId: 'santhoshguptha507@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Mr. Arukonda Siddartha',
      designation: 'Training & Placement Officer',
      department: 'MECH',
      mobileNumber: '9397666906',
      emailId: 'siddartha.arukonda@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Mr. R. Lakshman Naik',
      designation: 'Assistant Professor (c)',
      department: 'CSE, IT & CSD',
      mobileNumber: '9177644143',
      emailId: 'lakshman.ramavathu@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Dr. Rumana Abideen',
      designation: 'Assistant Professor (c)',
      department: 'EEE',
      mobileNumber: '8341199645',
      emailId: 'rumana.276@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Mr. R.D. Prasad',
      designation: 'Assistant Professor (c)',
      department: 'MECH',
      mobileNumber: '9603192848',
      emailId: 'prasadrd.215@gmail.com',
      category: 'Training & Placements',
    ),
    FacultyCoordinator(
      name: 'Dr. N. Satyashiva Prasad',
      designation: 'Assistant Professor (c)',
      department: 'CIVIL',
      mobileNumber: '9133612366',
      emailId: 'satya4249@gmail.com',
      category: 'Training & Placements',
    ),
  ];

  static const List<FacultyCoordinator> alumniCoordinators = [
    FacultyCoordinator(
      name: 'Dr. M. Soujanya',
      designation: 'Assistant Professor (c)',
      department: 'IT & CSD',
      mobileNumber: '9010610430',
      emailId: 'soujanyavedh@gmail.com',
      category: 'Alumni Affairs',
    ),
    FacultyCoordinator(
      name: 'Mrs. D. Bhagyalaxmi',
      designation: 'Assistant Professor (c)',
      department: 'CSE',
      mobileNumber: '7330858534',
      emailId: 'bhagyakmp519@gmail.com',
      category: 'Alumni Affairs',
    ),
    FacultyCoordinator(
      name: 'Dr. J. Ramchander',
      designation: 'Assistant Professor (c)',
      department: 'ECE',
      mobileNumber: '8247300529',
      emailId: 'ramchander4ece@gmail.com',
      category: 'Alumni Affairs',
    ),
    FacultyCoordinator(
      name: 'Dr. H. Lakshmi',
      designation: 'Assistant Professor (c)',
      department: 'EEE',
      mobileNumber: '9989660311',
      emailId: 'lakshmi.kucet@gmail.com',
      category: 'Alumni Affairs',
    ),
    FacultyCoordinator(
      name: 'Dr. A. Shirisha',
      designation: 'Assistant Professor (c)',
      department: 'MECH',
      mobileNumber: '9949904971',
      emailId: 'adupashirisha@gmail.com',
      category: 'Alumni Affairs',
    ),
    FacultyCoordinator(
      name: 'Mrs. M. Vennala',
      designation: 'Assistant Professor (c)',
      department: 'CIVIL',
      mobileNumber: '9515068515',
      emailId: 'manupativennala@gmail.com',
      category: 'Alumni Affairs',
    ),
  ];

  static const List<FacultyCoordinator> nssAndNccOfficers = [
    FacultyCoordinator(
      name: 'Dr. M. Soujanya',
      designation: 'NSS Program Officer',
      department: 'IT',
      mobileNumber: '9010610430',
      emailId: 'soujanyavedh@gmail.com',
      category: 'NSS',
    ),
    FacultyCoordinator(
      name: 'Dr. D. Sailaja',
      designation: 'NSS Program Officer',
      department: 'ECE',
      mobileNumber: '9866491832',
      emailId: 'sailajadasare@gmail.com',
      category: 'NSS',
    ),
    FacultyCoordinator(
      name: 'Lt. Dr. K. Vijay Kumar',
      designation: 'NCC ANO Officer',
      department: 'NCC',
      mobileNumber: '8074972649',
      emailId: 'drkvijay3004@gmail.com',
      category: 'NCC',
    ),
    FacultyCoordinator(
      name: 'Dr. B. Anil Kumar',
      designation: 'NCC Officer (CTO)',
      department: 'NCC - Airwing',
      mobileNumber: '9700381439',
      emailId: 'anil.kucet@gmail.com',
      category: 'NCC',
    ),
  ];

  /// Find coordinator by email
  static FacultyCoordinator? findByEmail(String email) {
    final lower = email.trim().toLowerCase();
    for (final c in academicCoordinators) {
      if (c.emailId?.toLowerCase() == lower) return c;
    }
    for (final c in placementOfficers) {
      if (c.emailId?.toLowerCase() == lower) return c;
    }
    for (final c in alumniCoordinators) {
      if (c.emailId?.toLowerCase() == lower) return c;
    }
    for (final c in mTechCoordinators) {
      if (c.emailId?.toLowerCase() == lower) return c;
    }
    for (final c in nssAndNccOfficers) {
      if (c.emailId?.toLowerCase() == lower) return c;
    }
    return null;
  }
}
