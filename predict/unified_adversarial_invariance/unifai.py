from keras.models import Model, load_model
import tensorflow as tf
import os


class UnifAI_Config(object):
    
    def __init__(self):
        self.model_config = None
        self.bias = False
        self.dropout_rate = -1.0
        
        self.local_weights_path = ''
        self.remote_weights_path = ''
        self.sync_frequency = -1
        
        self.losses = []
        self.loss_weights = []
        self.main_lr = -1.0
        self.adv_lr = -1.0
        self.optimizers = []
        self.metrics = {}
        
        self.training_schedule = ''
        
        self.batch_size = -1


class UnifAI_ModuleBuilder(object):
    
    def __init__(self, model_config, weights_dir, epoch_start):
        self.model_config = model_config
        self.weights_dir = weights_dir
        self.build_functions = {
            'encoder': self.model_config.encoder,
        }
        self.epoch_start = epoch_start
    
    def build_module(self, module_type, name=None,
                     build_kwargs={}, epoch=None, load_weights=True):
        # Default model-name is the same as model-type
        if name is None:
            name = module_type

        # Build module
        module = self.build_functions[module_type](name=name, **build_kwargs)

        # Load module
        weights_path = "{}/encoder-{:05d}.h5".format(self.weights_dir,self.epoch_start) 
        module = load_model(weights_path)

        return module


class UnifAI(object):
    
    def __init__(self, config, epoch_start):
        self.config = config
        self.model_config = self.config.model_config  # alias
        self.epoch_start = epoch_start
        self.module_builder = UnifAI_ModuleBuilder(
            self.model_config, self.config.remote_weights_path, self.epoch_start
        )
        
        self.encoder = None
        self.model_inference = None
    
    def build_model_inference(self, checkpoint_epoch=None):
        if self.model_inference is None:
            device = '/gpu:0'
            with tf.device(device):
                self.encoder = self.module_builder.build_module(
                    'encoder', epoch=checkpoint_epoch
                )
                
                x = self.encoder.inputs[0]
                e1, e2 = self.encoder(x)
                
                self.model_inference = Model(x, [e1,e2])

    def get_embed(self, data):
        assert self.model_inference is not None, 'run build_model_inference() first'

        model_enc1 = Model(inputs=self.model_inference.input,
                          outputs=self.model_inference.outputs[0])
        model_enc2 = Model(inputs=self.model_inference.input,
                          outputs=self.model_inference.outputs[1])

        return model_enc1.predict(data, batch_size=32), model_enc2.predict(data, batch_size=32) 
