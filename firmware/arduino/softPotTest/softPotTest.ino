//Using these softpots with a 10k pulldown https://learn.sparkfun.com/tutorials/softpot-hookup-guide

const byte sliderIn[2] = {A6, A7};

int sliderVals[2] = {0, 0};
int oldSliderVals[2] = {0, 0};
int sliderLowVal = 10;
int sliderHighVal = 1013;

void setup()
{
  Serial.begin(9600);
  for (int i = 0; i < 2; i++) {
    pinMode(sliderIn[i], INPUT);
  }
}

void loop()
{
  readSliders();
  delay(100);
}

void readSliders() {
  for (int i = 0; i < 2; i++) {
    int sliderVal = analogRead(sliderIn[i]);
    if ( sliderVal >= sliderLowVal && sliderVal <= sliderHighVal) {
      sliderVals[i] = map(sliderVal, sliderLowVal, sliderHighVal, 0, 100);
    }
    if (oldSliderVals[i] != sliderVals[i]) {
      oldSliderVals[i] = sliderVals[i];
      Serial.print("Slider");
      Serial.print(i);
      Serial.print(" is ");
      Serial.print(sliderVals[i]);
      Serial.print(" actual val is ");
      Serial.println(sliderVal);
    }
  }
}

