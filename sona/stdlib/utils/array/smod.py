"""Sona standard library: utils.array.smod"""

# Array module implementation for Sona v0.5.1

class ArrayModule:
    """Wrapper class for array operations in Sona"""
    
    def __init__(self):
        self.arrays = {}
        self.array_counter = 0
    
    def new(self):
        """Create a new array"""
        self.array_counter += 1
        self.arrays[self.array_counter] = []
        return self.array_counter
    
    def get(self, array_id, index):
        """Get item at index from array"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
        
        if index < 0 or index >= len(self.arrays[array_id]):
            raise IndexError(f"Index {index} out of bounds for array with length {len(self.arrays[array_id])}")
            
        return self.arrays[array_id][index]
    
    def set(self, array_id, index, value):
        """Set item at index in array"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
            
        if index < 0:
            raise IndexError(f"Negative index {index} not allowed")
            
        # Extend array if needed
        array = self.arrays[array_id]
        while index >= len(array):
            array.append(None)
            
        array[index] = value
        return value
    
    def push(self, array_id, value):
        """Add item to the end of array"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
            
        self.arrays[array_id].append(value)
        return len(self.arrays[array_id])
    
    def pop(self, array_id):
        """Remove and return the last item"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
            
        if not self.arrays[array_id]:
            raise IndexError("Cannot pop from empty array")
            
        return self.arrays[array_id].pop()
    
    def length(self, array_id):
        """Get array length"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
            
        return len(self.arrays[array_id])
    
    def to_list(self, array_id):
        """Convert to Python list"""
        if array_id not in self.arrays:
            raise ValueError(f"Array {array_id} does not exist")
            
        return self.arrays[array_id].copy()

# Create the singleton instance
array = ArrayModule()

# For debugging
print("[DEBUG] array module loaded")
