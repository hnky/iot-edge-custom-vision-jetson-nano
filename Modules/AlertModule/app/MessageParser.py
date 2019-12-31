
def highestProbabilityTagMeetingThreshold(message, threshold):
    highestProbabilityTag = 'none'
    highestProbability = 0
    for prediction in message['predictions']:
        if prediction['probability'] > highestProbability and prediction['probability'] > threshold:
            highestProbability = prediction['probability']
            highestProbabilityTag = prediction['tagName']
    return highestProbabilityTag
