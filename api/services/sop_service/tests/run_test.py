# api/services/sop_service/tests/run_test.py
# Simple test runner for SOP service integration tests

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from .test_sop_service_integration import TestSopServiceIntegration


def main():
    """Run the SOP service integration test"""
    print("🧪 Running SOP Service Integration Test")
    print("=" * 60)
    
    try:
        # Create test instance and run all tests
        test_instance = TestSopServiceIntegration()
        test_instance.run_all_tests()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print("   ✅ Document creation with blocks")
        print("   ✅ Title block addition")
        print("   ✅ Description block addition") 
        print("   ✅ Section header addition")
        print("   ✅ Step blocks addition (2 steps)")
        print("   ✅ Block operations (CRUD)")
        print("   ✅ Document assembly (HTML, Markdown, Plain Text, JSON)")
        print("   ✅ Document validation")
        print("   ✅ SOP service integration")
        
        print("\n🔧 Tested Functions:")
        print("   - BlockService.add_block()")
        print("   - BlockService.add_step_block()")
        print("   - BlockService.get_document_blocks()")
        print("   - BlockService.get_block()")
        print("   - BlockService.update_block()")
        print("   - BlockService.duplicate_block()")
        print("   - BlockService.reorder_blocks()")
        print("   - BlockService.delete_block()")
        print("   - DocumentAssembler.assemble_document()")
        print("   - DocumentAssembler.validate_document_structure()")
        print("   - SopService initialization")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 