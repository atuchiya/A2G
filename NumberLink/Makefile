TARGET = sim
OBJS = $(CPPS:.cpp=.o)
CPPS = $(wildcard *.cpp)
CXX = g++
CXXFLAGS = -O3 -Wall -Wno-unknown-pragmas -Wno-unused-label -DSOFTWARE -DCALCTIME

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) -O3 -o $@ $(OBJS)

run:
	python3 ../NLGenerator.py -x 20 -y 20 -z 6 -l 100;\
	python3 ./gen_boardstr.py Q-20x20x5_100_10.txt |\
	./$(TARGET) -


clean:
	rm *.o
	rm $(TARGET)
