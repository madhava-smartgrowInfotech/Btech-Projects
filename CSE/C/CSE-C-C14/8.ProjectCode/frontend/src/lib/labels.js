// Backend labels are REAL / AI_GENERATED; the UI says "AI-generated".
export const isReal = (label) => label === 'REAL'
export const labelText = (label) => (label === 'REAL' ? 'Real' : label === 'AI_GENERATED' ? 'AI-generated' : label)
export const labelTone = (label) => (label === 'REAL' ? 'mint' : label === 'AI_GENERATED' ? 'rose' : 'neutral')

export const MODEL_NAMES = {
  efficientnet_a1: 'EfficientNet A1',
  efficientnet_a2: 'EfficientNet A2',
  resnet50_b: 'ResNet50 B',
  mobilenetv3_c: 'MobileNetV3 C',
}
export const BRANCH_TO_MODEL = { a1: 'efficientnet_a1', a2: 'efficientnet_a2', b: 'resnet50_b', c: 'mobilenetv3_c' }
export const CONDITION_NAMES = { clean: 'Clean', jpeg: 'JPEG q=60', resize: '2× resample', blur: 'Gaussian blur', noise: 'Noise' }
export const isDemoData = (dataset) => /synthetic|demo/i.test(dataset || '')
