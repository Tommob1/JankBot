import cv2
import mediapipe as mp
mp_drawing=mp.solutions.drawing_utils
mp_drawing_styles=mp.solutions.drawing_styles
mphands=mp.solutions.hands

cap=cv2.VideoCapture(0)
hands=mphands.Hands()
while True:
	data,image=cap.read()
	image=cv2.cvtColor(cv2.flip(image,1),cv2.COLOR_BGR2RGB)
	results=hands.process(image)
	image=cv2.cvtColor(image,cv2.COLOR_RGB2BGR)
	if results.multi_hand_landmarks:
		for hand_landmarks in results.multi_hand_landmarks:
			mp_drawing.draw_landmarks(
				image,
				hand_landmarks,mphands.HAND_CONNECTIONS,
				mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=5, circle_radius=5),
				mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=5))
	cv2.imshow('Handtracker', image)
	cv2.waitKey(1)