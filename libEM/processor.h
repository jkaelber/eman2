/**
 * $Id$
 */
#ifndef eman_processor_h__
#define eman_processor_h__ 1

#include "emobject.h"
#include "util.h"

#include <float.h>
#include <limits.h>

using std::vector;
using std::map;
using std::string;

namespace EMAN
{
	class EMData;
	class Transform3D;

	/** Typical usage of Processors are as follows:
     *
     *   - How to get all the processor names
     *@code
     *      vector<string> all_processors = Factory<Processor>::get_list();
     @endcode
     *   - How to use a processor
     *@code
     *      EMData *img = ...;
     *      img->process("PROCESSORNAME", Dict("sigma", 12));
     @endcode
     *   - How to define a new XYZProcessor \n
     *      XYZProcessor should either extend the base class 'Processor' or a
     *      subclass of 'Processor'. At a minimum, it should define:
	 *      (Please replace 'XYZ' with your own class name).
	 *@code
     *          string get_name() const { return "processorname"; }
     *          static Processor *NEW() { return XYZProcessor(); }
	 @endcode
	 *      If XYZProcessor is a parent class, it should define:
	 *@code
	 *          static string get_group_desc();
	 @endcode
	 *      Otherwise, it should define:
	 *@code
	 *          string get_desc() const;
	 @endcode
     *      If XYZProcessor need parameters not defined by its parent
     *      class, it should define:
	 *@code
	 *          Dict get_params() const;
	 *          void set_params(const Dict & new_params);
     *          TypeDict get_param_types() const;
     @endcode
     */
	class Processor
	{
	  public:
		virtual ~ Processor()
		{
		}

		/** To process an image in-place.
		 * @param image The image to be processed.
		 */
		virtual void process(EMData *image)
		{
		}

		/** To process multiple images using the same algorithm.
		 * @param images Multiple images to be processed.
		 */
		virtual void process_list(vector < EMData * > & images)
		{
			for (size_t i = 0; i < images.size(); i++) {
				process(images[i]);
			}
		}

		/** Get the processor's name. Each processor is identified by a unique name.
		 * @return The processor's name.
		 */
		virtual string get_name() const = 0;
		
		/** Get the processor parameters in a key/value dictionary.
		 * @return A key/value pair dictionary containing the parameters.
		 */
		virtual Dict get_params() const
		{
			return params;
		}
		
		/** Set the processor parameters using a key/value dictionary.
		 * @param new_params A dictionary containing the new parameters.
		 */
		virtual void set_params(const Dict & new_params)
		{
			params = new_params;
		}
		
		/** Get processor parameter information in a dictionary. Each
		 * parameter has one record in the dictionary. Each record
		 * contains its name, data-type, and description.
		 *
		 * @return A dictionary containing the parameter info.
		 */	 
		virtual TypeDict get_param_types() const
		{
			return TypeDict();
		}

		/** Get the description of this group of processors. This
		 * function is defined in a parent class. It gives a
		 * introduction to a group of processors.
		 *
		 * @return The description of this group of processors.
		 */
		static string get_group_desc()
		{
			return "EMAN processors are in-place image processors. You may apply a processor to process a single image or process multiple images. Processor class is the base class for all processor. <br> \
The basic design of EMAN Processors: <br>\
    1) Each Processor class defines an image-processinging algorithm. <br>\
    2) All the Processor classes in EMAN are managed by a Factory pattern. So each Processor class must define: <br> a) a unique name to idenfity itself in the factory. <br>b) a static method to register itself in the factory.<br>\
    3) Each Processor class defines its own parameter set.<br>\
    4) Each Processor class defines functions to return its documentation including parameter information, and processor description. These functions enable EMAN to generate processor manuals dynamically.";
		}

		/** Get the descrition of this specific processor. This function
		 * must be overwritten by a subclass.
		 *
		 * @return The description of this processor.
		 */
		virtual string get_desc() const = 0;

		/** Fourier filter Processor type enum.
		 *  New Fourier filter processors are computed in a single function,
		 *  EMFourierFilterFunc, that uses a large switch statement to 
		 *  apply the correct filter processor.  This enum specifies the
		 *  filter processor to be applied.
		 */
		enum fourier_filter_types {
			TOP_HAT_LOW_PASS,
			TOP_HAT_HIGH_PASS,
			TOP_HAT_BAND_PASS,
			TOP_HOMOMORPHIC,
			GAUSS_LOW_PASS,
			GAUSS_HIGH_PASS,
			GAUSS_BAND_PASS,
			GAUSS_INVERSE,
			GAUSS_HOMOMORPHIC,
			BUTTERWORTH_LOW_PASS,
			BUTTERWORTH_HIGH_PASS,
			BUTTERWORTH_HOMOMORPHIC,
			KAISER_I0,
			KAISER_SINH,
			KAISER_I0_INVERSE,
			KAISER_SINH_INVERSE,
			TANH_LOW_PASS,
			TANH_HIGH_PASS,
			TANH_HOMOMORPHIC,
			TANH_BAND_PASS,
			RADIAL_TABLE
		};

		/** Compute a Fourier-filter processed image in place.
		 *
		 *  @par Purpose: Apply selected Fourier space processor to 1-,2-, or 3-D image.
		 *  @par Method: 
		 *  
		 *  @param     fimage  Input image object to be processed, either
		 *                     a real-space image or a Fourier-space image.
		 *                     Image may be 1-, 2-, or 3-dimensional.  The
		 *                     original input image is not touched by 
		 *                     this routine.
		 *
		 *  @param[in] params  Processor parameters.  Different processors require
		 *                     different parameters, so we this routine accepts
		 *                     a dictionary of parameters and looks up the
		 *                     appropriate params for the chosen processor at
		 *                     run time.  All processors use the "dopad" 
		 *                     parameter to determine whether the 
		 *                     Fourier workspace array should be zero-
		 *                     padded to twice the original length
		 *                     (dopad == 1) or not zero-padded at all
		 *                     (dopad == 0).
		 *  @return No explicit return.  The image fimage is modified
		 *  in place.
		 */
		static void
		EMFourierFilterInPlace(EMData* fimage, Dict params) {
			bool doInPlace = true;
			EMFourierFilterFunc(fimage, params, doInPlace);
		}
		
		/** Compute a Fourier-processor processed image without altering the original image.
		 *
		 *  @par Purpose: Apply selected Fourier space processor to 1-,2-, or 3-D image.
		 *  @par Method: 
		 *  
		 *  @param     fimage  Input image object to be processeded, either
		 *                     a real-space image or a Fourier-space image.
		 *                     Image may be 1-, 2-, or 3-dimensional.  
		 *
		 *  @param[in] params  Processor parameters.  Different processors require
		 *                     different parameters, so we this routine accepts
		 *                     a dictionary of parameters and looks up the
		 *                     appropriate params for the chosen processor processor at
		 *                     run time.  All processors use the "dopad" 
		 *                     parameter to determine whether the 
		 *                     Fourier workspace array should be zero-
		 *                     padded to twice the original length
		 *                     (dopad == 1) or not zero-padded at all
		 *                     (dopad == 0).
		 *  @return 1-, 2-, or 3-dimensional filter processed image.  If the
		 *          input image is a real-space image, then the returned
		 *          output image will also be a real-space image.  
		 *          Similarly, if the input image is already a Fourier image,
		 *          then the output image will be a Fourier image.
		 */
		static EMData*
		EMFourierFilter(EMData* fimage, Dict params) {
			bool doInPlace = false;
			return EMFourierFilterFunc(fimage, params, doInPlace);
		}
		
	  private:
		/** Compute a Fourier-filter processed image.
		 *  This function is called by either of the convience functions
		 *  EMFourierFilter or EMFourierFilterInPlace.
		 *
		 *  @par Purpose: Apply selected Fourier space processor to 1-,2-, or 3-D image.
		 *  @par Method: 
		 *  
		 *  @param     fimage  Input image object to be processed, either
		 *                     a real-space image or a Fourier-space image.
		 *                     Image may be 1-, 2-, or 3-dimensional.  Image
		 *                     fimage will not be changed unless 
		 *                     inplace == true.
		 *  @param[in] params  Processor parameters.  Different processor processors require
		 *                     different parameters, so we this routine accepts
		 *                     a dictionary of parameters and looks up the
		 *                     appropriate params for the chosen processor processor at
		 *                     run time.  All processors use the "dopad" 
		 *                     parameter to determine whether the 
		 *                     Fourier workspace array should be zero-
		 *                     padded to twice the original length
		 *                     (dopad == 1) or not zero-padded at all
		 *                     (dopad == 0).
		 *  @param[in] doInPlace Inplace flag.  If this flag is true then 
		 *                     fimage will contain the processeded image 
		 *                     when this function returns.
		 *
		 *  @return 1-, 2-, or 3-dimensional filter processed image.  If the
		 *          input image is a real-space image, then the returned
		 *          output image will also be a real-space image.  
		 *          Similarly, if the input image is already a Fourier image,
		 *          then the output image will be a Fourier image.
		 *          In either case, if inplace == true then the output
		 *          image (pointer) will be the same as the input image
		 *          (pointer).
		 */
		static EMData* 
		EMFourierFilterFunc(EMData* fimage, Dict params, bool doInPlace=true);
		
	  protected:
		mutable Dict params;
	};

	class ImageProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		static string get_group_desc()
		{
			return "An Image Processor defines a way to create a processor image. The processor image is used to multiply the input-image in the fourier space. ImageFilter class is the base class. Each specific ImageFilter class must define function create_processor_image(). ";
		}
		
	  protected:
		virtual EMData * create_processor_image() const = 0;
	};



	class NewFourierProcessor:public Processor
	{
	  public:
		//virtual void process(EMData * image);
		
		static string get_group_desc()
		{
			return "Fourier Filter Processors are frequency domain processors. The input image can be either real or Fourier, and the output processed image format corresponds to that of the input file. FourierFilter class is the base class of fourier space processors. The processors can be either low-pass, high-pass, band-pass, or homomorphic. The processor parameters are in absolute frequency units, valid range is ]0,0.5], where 0.5 is Nyquist freqeuncy. ";
		}
	};

	class NewLowpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.tophat"; }
		static Processor *NEW()
		{ return new NewLowpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Lowpass top-hat filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TOP_HAT_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			return d;
		}
		
	};

	class NewHighpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.tophat"; }
		static Processor *NEW()
		{ return new NewHighpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Highpass top-hat filter applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TOP_HAT_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			return d;
		}
	};

	class NewBandpassTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.tophat"; }
		static Processor *NEW()
		{ return new NewBandpassTopHatProcessor(); }
		string get_desc() const
		{
			return "Bandpass top-hat filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TOP_HAT_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};

	class NewHomomorphicTopHatProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.tophat"; }
		static Processor *NEW()
		{ return new NewHomomorphicTopHatProcessor(); }
		string get_desc() const
		{
			return "Homomorphic top-hat filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TOP_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("Value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};

	class NewLowpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.gauss"; }
		static Processor *NEW()
		{ return new NewLowpassGaussProcessor(); }
		string get_desc() const
		{
			return "Lowpass Gauss filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = GAUSS_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};

	class NewHighpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.gauss"; }
		static Processor *NEW()
		{ return new NewHighpassGaussProcessor(); }
		string get_desc() const
		{
			return "Highpass Gauss filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = GAUSS_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};

	class NewBandpassGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.gauss"; }
		static Processor *NEW()
		{ return new NewBandpassGaussProcessor(); }
		string get_desc() const
		{
			return "Bandpass Gauss filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = GAUSS_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Sigma", EMObject::FLOAT, "Gaussian sigma.");
			d.put("Center", EMObject::FLOAT, "Gaussian center.");
			return d;
		}
	};

	class NewHomomorphicGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.gauss"; }
		static Processor *NEW()
		{ return new NewHomomorphicGaussProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Gauss filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = GAUSS_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Sigma", EMObject::FLOAT, "Gaussian sigma.");
			d.put("Value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};

	class NewInverseGaussProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.gaussinverse"; }
		static Processor *NEW()
		{ return new NewInverseGaussProcessor(); }
		string get_desc() const
		{
			return "Divide by a Gaussian in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = GAUSS_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Sigma", EMObject::FLOAT, "Gaussian sigma.");
			return d;
		}
	};

	class InverseKaiserI0Processor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.kaiserI0inverse"; }
		static Processor *NEW()
		{ return new InverseKaiserI0Processor(); }
		string get_desc() const
		{
			return "Divide by a Kaiser-Bessel I0 func in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = KAISER_I0_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
	};

	class InverseKaiserSinhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.kaisersinhinverse"; }
		static Processor *NEW()
		{ return new InverseKaiserSinhProcessor(); }
		string get_desc() const
		{
			return "Divide by a Kaiser-Bessel Sinh func in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = KAISER_SINH_INVERSE;
			EMFourierFilterInPlace(image, params); 
		}
	};

	class NewRadialTableProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.radialtable"; }
		static Processor *NEW()
		{ return new NewRadialTableProcessor(); }
		string get_desc() const
		{
			return "Filter with tabulated data in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = RADIAL_TABLE;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Table", EMObject::FLOATARRAY, "Tabulated filter data.");
			return d;
		}
	};

	class NewLowpassButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.butterworth"; }
		static Processor *NEW()
		{ return new NewLowpassButterworthProcessor(); }
		string get_desc() const
		{
			return "Lowpass Butterworth filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = BUTTERWORTH_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};

	class NewHighpassButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.butterworth"; }
		static Processor *NEW()
		{ return new NewHighpassButterworthProcessor(); }
		string get_desc() const
		{
			return "Highpass Butterworth filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = BUTTERWORTH_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			return d;
		}
	};

	class NewHomomorphicButterworthProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.butterworth"; }
		static Processor *NEW()
		{ return new NewHomomorphicButterworthProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Butterworth filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = BUTTERWORTH_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("Value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};

	class NewLowpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.lowpass.tanh"; }
		static Processor *NEW()
		{ return new NewLowpassTanhProcessor(); }
		string get_desc() const
		{
			return "Lowpass tanh filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TANH_LOW_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("Fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};

	class NewHighpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.highpass.tanh"; }
		static Processor *NEW()
		{ return new NewHighpassTanhProcessor(); }
		string get_desc() const
		{
			return "Highpass tanh filter processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TANH_HIGH_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("Fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};

	class NewHomomorphicTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.homomorphic.tanh"; }
		static Processor *NEW()
		{ return new NewHomomorphicTanhProcessor(); }
		string get_desc() const
		{
			return "Homomorphic Tanh processor applied in Fourier space";
		}
		void process(EMData* image) {
			params["FilterType"] = TANH_HOMOMORPHIC;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] cut-off frequency.");
			d.put("Fall_off", EMObject::FLOAT, "Tanh decay rate.");
			d.put("Value_at_zero_frequency", EMObject::FLOAT, "Value at zero frequency.");
			return d;
		}
	};

	class NewBandpassTanhProcessor:public NewFourierProcessor
	{
	  public:
		string get_name() const
		{ return "filter.bandpass.tanh"; }
		static Processor *NEW()
		{ return new NewBandpassTanhProcessor(); }
		string get_desc() const
		{
			return "Bandpass tanh processor applied in Fourier space.";
		}
		void process(EMData* image) {
			params["FilterType"] = TANH_BAND_PASS;
			EMFourierFilterInPlace(image, params); 
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("Low_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] low cut-off frequency.");
			d.put("Low_fall_off", EMObject::FLOAT, "Tanh low decay rate.");
			d.put("High_cutoff_frequency", EMObject::FLOAT, "Absolute [0,0.5] high cut-off frequency.");
			d.put("High_fall_off", EMObject::FLOAT, "Tanh high decay rate.");
			d.put("Fall_off", EMObject::FLOAT, "Tanh decay rate.");
			return d;
		}
	};

	class FourierProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		static string get_group_desc()
		{
			return "Fourier Filter processors are a group of processor in the frequency domain. Before using such processors on an image, the image must be transformed from real space to the fourier space. FourierProcessor class is the base class of fourier space processors. Each specific processor is either a lowpass filter processor, or a highpass filter processor, or neighter. The unit of lowpass and highpass parameters are in terms of Nyquist, valid range is [0,0.5]. ";
		}
		
	  protected:
		virtual void create_radial_func(vector < float >&radial_mask) const = 0;
	};

	class LowpassFourierProcessor:public FourierProcessor
	{
	  public:
		LowpassFourierProcessor():lowpass(0)
		{
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			lowpass = params["lowpass"];
//			printf("%s %f\n",params.keys()[0].c_str(),lowpass);
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("lowpass", EMObject::FLOAT, "Processor radius in terms of Nyquist (0-.5)");
			return d;
		}
		
		static string get_group_desc() 
		{
			return "Low-pass processor attenuates amplitudes at high spatial frequencies. It has the result of blurring the image, and of eliminating sharp edges and noise. The base class for all low pass fourier processors.";
		}
		
	  protected:
		float lowpass;
	};

	class HighpassFourierProcessor:public FourierProcessor
	{
	  public:
		HighpassFourierProcessor():highpass(0)
		{
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			highpass = params["highpass"];
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("highpass", EMObject::FLOAT, "Processor radius in terms of Nyquist (0-.5)");
			return d;
		}
		
		static string get_group_desc()
		{
			return "High-pass processor is rotationally symmetric 2D function. It attenuates amplitudes at low spatial frequencies, and increases amplitudes for high spatial frequencies. It has the result of enhancing the edges in the image while suppressing all slow-moving variations.	<br> HighpassFourierProcessor class is the base class for all high pass fourier processors.";
		}
		
	  protected:
		float highpass;
	};

	class LowpassSharpCutoffProcessor:public LowpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.lowpass.sharp";
		}

		static Processor *NEW()
		{
			return new LowpassSharpCutoffProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: if x <= lowpass, f(x) = 1; else f(x) = 0;";
		}
		
	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class HighpassSharpCutoffProcessor:public HighpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.highpass.sharp";
		}

		static Processor *NEW()
		{
			return new HighpassSharpCutoffProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: if x >= highpass, f(x) = 1; else f(x) = 0;";
		}

		
	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class LowpassGaussProcessor:public LowpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.lowpass.gaussian";
		}

		static Processor *NEW()
		{
			return new LowpassGaussProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: if lowpass > 0, f(x) = exp(-x*x/(lowpass*lowpass)); else f(x) = exp(x*x/(lowpass*lowpass));";
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class HighpassGaussProcessor:public HighpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.highpass.gaussian";
		}
		static Processor *NEW()
		{
			return new HighpassGaussProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: f(x) = 1.0-exp(-x*x/(highpass*highpass);";
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class LowpassTanhProcessor:public LowpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.lowpass.tanh";
		}
		static Processor *NEW()
		{
			return new LowpassTanhProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: f(x)=tanh(lowpass-x)/2.0 + 0.5;";
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};


	class HighpassTanhProcessor:public HighpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.highpass.tanh";
		}
		static Processor *NEW()
		{
			return new HighpassTanhProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: f(x)=tanh(x-highpass)/2.0+0.5;";
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class HighpassButterworthProcessor:public HighpassFourierProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.highpass.butterworth";
		}
		static Processor *NEW()
		{
			return new HighpassButterworthProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: f(x) = 1/(1+t*t);";
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;
	};

	class LinearRampProcessor:public FourierProcessor
	{
	  public:
		LinearRampProcessor():intercept(0), slope(0)
		{
		}

		string get_name() const
		{
			return "eman1.filter.ramp";
		}
		static Processor *NEW()
		{
			return new LinearRampProcessor();
		}

		string get_desc() const
		{
			return "processor radial function: f(x) = slope * x + intercept;";
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			intercept = params["intercept"];
			slope = params["slope"];
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("intercept", EMObject::FLOAT);
			d.put("slope", EMObject::FLOAT);
			return d;
		}

	  protected:
		void create_radial_func(vector < float >&radial_mask) const;

	  private:
		float intercept;
		float slope;
	};

	class RealPixelProcessor:public Processor
	{
	  public:
		RealPixelProcessor():value(0), maxval(1), mean(0), sigma(0)
		{
		}
		void process(EMData * image);

		void set_params(const Dict & new_params)
		{
			params = new_params;
			if (params.size() == 1) {
				vector < EMObject > dict_values = params.values();
				value = dict_values[0];
			}
		}

		static string get_group_desc()
		{
			return "The base class for real space processor working on individual pixels. The processor won't consider the pixel's coordinates and neighbors.";
		}
		
	  protected:
		virtual void process_pixel(float *x) const = 0;
		virtual void calc_locals(EMData *)
		{
		}
		virtual void normalize(EMData *) const
		{
		}

		float value;
		float maxval;
		float mean;
		float sigma;
	};

	class AbsoluateValueProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.absvalue";
		}
		static Processor *NEW()
		{
			return new AbsoluateValueProcessor();
		}
	  protected:
		void process_pixel(float *x) const
		{
			*x = fabs(*x);
		}

		string get_desc() const
		{
			return "f(x) = |x|";
		}
		
	};

	class BooleanProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.threshold.notzero";
		}
		static Processor *NEW()
		{
			return new BooleanProcessor();
		}

		string get_desc() const
		{
			return "f(x) = 0 if x = 0; f(x) = 1 if x != 0;";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			if (*x != 0)
			{
				*x = 1.0;
			}
		}
	};

	class ValueSquaredProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.squared";
		}
		static Processor *NEW()
		{
			return new ValueSquaredProcessor();
		}


		string get_desc() const
		{
			return "f(x) = x * x;";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			(*x) *= (*x);
		}
	};

	class ValueSqrtProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.sqrt";
		}
		static Processor *NEW()
		{
			return new ValueSqrtProcessor();
		}

		string get_desc() const
		{
			return "f(x) = sqrt(x)";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			*x = sqrt(*x);
		}
	};

	class ToZeroProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.threshold.belowtozero";
		}
		static Processor *NEW()
		{
			return new ToZeroProcessor();
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("minval", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x) = x if x >= minval; f(x) = 0 if x < minval.";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			if (*x < value) {
				*x = 0;
			}
		}
	};

	class BinarizeProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.threshold.binary";
		}
		static Processor *NEW()
		{
			return new BinarizeProcessor();
		}
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("value", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x) = 0 if x < value; f(x) = 1 if x >= value.";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			if (*x < value)
			{
				*x = 0;
			}
			else
			{
				*x = 1;
			}
		}
	};

	class CollapseProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.threshold.compress";
		}
		static Processor *NEW()
		{
			return new CollapseProcessor();
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			range = params["range"];
			value = params["value"];
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("range", EMObject::FLOAT);
			d.put("value", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x): if v-r<x<v+r -> v; if x>v+r -> x-r; if x<v-r -> x+r";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			if (*x>range+value) *x-=range;
			else if (*x<range-value) *x+=range;
			else *x=value;
		}
		float range;
	};

	class LinearXformProcessor:public RealPixelProcessor
	{
	  public:
		LinearXformProcessor():shift(0), scale(0)
		{
		}

		string get_name() const
		{
			return "eman1.math.linear";
		}
		static Processor *NEW()
		{
			return new LinearXformProcessor();
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			shift = params.get("shift");
			scale = params.get("scale");
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("shift", EMObject::FLOAT);
			d.put("scale", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "linear transform processor: f(x) = x * scale + shift";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			*x = (*x) * scale + shift;
		}

	  private:
		float shift;
		float scale;
	};

	class ExpProcessor:public RealPixelProcessor
	{
	  public:
		ExpProcessor():low(0), high(0)
		{
		}

		string get_name() const
		{
			return "eman1.math.exp";
		}

		static Processor *NEW()
		{
			return new ExpProcessor();
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			low = params.get("low");
			high = params.get("high");
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low", EMObject::FLOAT);
			d.put("high", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x) = exp( x / low - high)";
		}

	  protected:
	/**
	 * '40' is used to avoid floating number overflow.
	 */
		void process_pixel(float *x) const
		{
			float v = *x / low - high;
			if (v > 40) {
				v = 40;
			}
			*x = exp(v);
		}

	  private:
		float low;
		float high;
	};

	class RangeThresholdProcessor:public RealPixelProcessor
	{
	  public:
		RangeThresholdProcessor():low(0), high(0)
		{
		}

		string get_name() const
		{
			return "eman1.threshold.binaryrange";
		}
		static Processor *NEW()
		{
			return new RangeThresholdProcessor();
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			low = params.get("low");
			high = params.get("high");
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("low", EMObject::FLOAT);
			d.put("high", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x) = 1 if (low <= x <= high); else f(x) = 0;";
		}
		
	  protected:
		void process_pixel(float *x) const
		{
			if (*x >= low && *x <= high) {
				*x = 1;
			}
			else {
				*x = 0;
			}
		}
	  private:
		float low;
		float high;

	};

	class SigmaProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.sigma";
		}
		static Processor *NEW()
		{
			return new SigmaProcessor();
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;
			value1 = params.get("value1");
			value2 = params.get("value2");
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("value1", EMObject::FLOAT);
			d.put("value2", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "f(x) = mean if x<(mean-v2*sigma) or x>(mean+v1*sigma); else f(x) = x;";
		}

	  protected:
		void process_pixel(float *x) const
		{
			if (*x < th1 || *x > th2)
			{
				*x = mean;
			}
		}
		void calc_locsl()
		{
			th1 = mean - value2 * sigma;
			th2 = mean + value1 * sigma;
		}

	  private:
		float value1;
		float value2;
		float th1;
		float th2;
	};

	class LogProcessor:public RealPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.log";
		}
		static Processor *NEW()
		{
			return new LogProcessor();
		}

		string get_desc() const
		{
			return "f(x) = log10(x/max_pixel) if x > 0; else f(x) = 0;";
		}

	  protected:
		void process_pixel(float *x) const
		{
			if (*x > 0)
			{
				*x = log10(*x / maxval);
			}
			else
			{
				*x = 0;
			}
		}
	};

	class CoordinateProcessor:public Processor
	{
	  public:
		CoordinateProcessor():nx(0), ny(0), nz(0), mean(0), sigma(0), maxval(0), is_complex(false)
		{
		}
		void process(EMData * image);

		static string get_group_desc()
		{
			return "CoordinateProcessor applies processing based on a pixel's value and it coordinates. This is the base class. Specific coordinate processor should implement process_pixel().";
		}

	  protected:
		virtual void process_pixel(float *pixel, int xi, int yi, int zi) const = 0;
		virtual void calc_locals(EMData *)
		{
		}
		virtual bool is_valid() const
		{
			return true;
		}

		int nx;
		int ny;
		int nz;
		float mean;
		float sigma;
		float maxval;

		bool is_complex;
	};

	class CircularMaskProcessor:public CoordinateProcessor
	{
	  public:
		CircularMaskProcessor():inner_radius(0), outer_radius(0), inner_radius_square(0),
			outer_radius_square(0), dx(0), dy(0), dz(0), xc(0), yc(0), zc(0)
		{
		}

		void set_params(const Dict & new_params)
		{
			params = new_params;

			if (params.has_key("inner_radius")) {
				inner_radius = params["inner_radius"];
				inner_radius_square = inner_radius * inner_radius;
			}
			else {
				inner_radius = -1;
				inner_radius_square = -1;
			}

			if (params.has_key("outer_radius")) {
				outer_radius = params["outer_radius"];
				outer_radius_square = outer_radius * outer_radius;
			}
			else {
				outer_radius = INT_MAX;
				outer_radius_square = INT_MAX;
			}

			if (params.has_key("xc")) xc = params["xc"];
			if (params.has_key("yc")) yc = params["yc"];
			if (params.has_key("zc")) zc = params["zc"];
			if (params.has_key("dx")) dx = params["dx"];
			if (params.has_key("dy")) dy = params["dy"];
			if (params.has_key("dz")) dz = params["dz"];
		}
		
		string get_desc() const
		{
			return "CircularMaskProcessor applies a circular mask to the data.This is the base class for specific circular mask processors.Its subclass must implement process_dist_pixel().";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;

			d.put("inner_radius", EMObject::INT, "inner mask radius. optional, default=-1");
			d.put("outer_radius", EMObject::INT, "outer mask radius");

			d.put("dx", EMObject::FLOAT,
				  "Modify mask center by dx relative to the default center nx/2");
			d.put("dy", EMObject::FLOAT,
				  "Modify mask center by dy relative to the default center ny/2");
			d.put("dz", EMObject::FLOAT,
				  "Modify mask center by dz relative to the default center nz/2");

			return d;
		}
	  protected:
		void calc_locals(EMData * image);

		bool is_valid() const
		{
			return (!is_complex);
		}

		void process_pixel(float *pixel, int xi, int yi, int zi) const
		{
			float dist = (xi - xc) * (xi - xc) + (yi - yc) * (yi - yc) + (zi - zc) * (zi - zc);
			process_dist_pixel(pixel, dist);
		}

		virtual void process_dist_pixel(float *pixel, float dist) const = 0;

		int inner_radius;
		int outer_radius;
		int inner_radius_square;
		int outer_radius_square;
		float dx, dy, dz;
		float xc, yc, zc;
	};

	class MaskSharpProcessor:public CircularMaskProcessor
	{
	  public:
		MaskSharpProcessor():value(0)
		{
		}

		string get_name() const
		{
			return "eman1.mask.sharp";
		}
		static Processor *NEW()
		{
			return new MaskSharpProcessor();
		}

		void set_params(const Dict & new_params)
		{
			CircularMaskProcessor::set_params(new_params);
			value = params["value"];
		}

		TypeDict get_param_types() const
		{
			TypeDict d = CircularMaskProcessor::get_param_types();
			d.put("value", EMObject::FLOAT, "step cutoff to this value.");
			return d;
		}
		
		string get_desc() const
		{
			return "step cutoff to a user-given value in both inner and outer circles.";
		}

	  protected:
		void process_dist_pixel(float *pixel, float dist) const
		{
			if (dist >= outer_radius_square || dist < inner_radius_square)
			{
				*pixel = value;
			}
		}

		float value;
	};

	
	class MaskEdgeMeanProcessor:public CircularMaskProcessor
	{							// 6
	  public:
		string get_name() const
		{
			return "eman1.mask.ringmean";
		}
		static Processor *NEW()
		{
			return new MaskEdgeMeanProcessor();
		}

		void set_params(const Dict & new_params)
		{
			CircularMaskProcessor::set_params(new_params);
			ring_width = params["ring_width"];
			if (ring_width == 0) {
				ring_width = 1;
			}
		}

		TypeDict get_param_types() const
		{
			TypeDict d = CircularMaskProcessor::get_param_types();
			d.put("ring_width", EMObject::INT, "The width of the mask ring.");
			return d;
		}

		string get_desc() const
		{
			return "A step cutoff to the the mean value in a ring centered on the outer radius";
		}

	  protected:
		void calc_locals(EMData * image);


		void process_dist_pixel(float *pixel, float dist) const
		{
			if (dist >= outer_radius_square){
				*pixel = ring_avg;
			}
		}

	  private:
		int ring_width;
		float ring_avg;
	};

	class MaskNoiseProcessor:public CircularMaskProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.mask.noise";
		}
		static Processor *NEW()
		{
			return new MaskNoiseProcessor();
		}

		string get_desc() const
		{
			return "fills masked region";
		}

	  protected:
		void process_dist_pixel(float *pixel, float dist) const
		{
			if (dist >= outer_radius_square || dist < inner_radius_square)
			{
				*pixel = Util::get_gauss_rand(mean, sigma);
			}
		}
	};

	class MaskGaussProcessor:public CircularMaskProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.mask.gaussian";
		}
		static Processor *NEW()
		{
			return new MaskGaussProcessor();
		}

		string get_desc() const
		{
			return "a gaussian falloff to zero, radius is the 1/e of the width.";
		}

	  protected:
		void process_dist_pixel(float *pixel, float dist) const
		{
			(*pixel) *= exp(-dist / outer_radius_square);
		}
	};

	class MaskGaussInvProcessor:public CircularMaskProcessor
	{
	  public:
		TypeDict get_param_types() const
		{
			TypeDict d = CircularMaskProcessor::get_param_types();
			d.put("gauss_width", EMObject::FLOAT);
			return d;
		}

		string get_name() const
		{
			return "eman1.math.gausskernelfix";
		}

		static Processor *NEW()
		{
			return new MaskGaussInvProcessor();
		}

		string get_desc() const
		{
			return "f(x) = f(x) / exp(-radius*radius * gauss_width / (ny*ny))";
		}

	  protected:
		void calc_locals(EMData *)
		{
			float gauss_width = params["gauss_width"];
			slice_value = gauss_width / (ny * ny);
		}

		void process_dist_pixel(float *pixel, float dist) const
		{
			(*pixel) /= exp(-dist * slice_value);
		}
	  private:
		float slice_value;
	};


	class MakeRadiusSquaredProcessor:public CircularMaskProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.toradiussqr";
		}
		static Processor *NEW()
		{
			return new MakeRadiusSquaredProcessor();
		}

		string get_desc() const
		{
			return "overwrites input, f(x) = radius * radius";
		}

	  protected:
		void process_dist_pixel(float *pixel, float dist) const
		{
			*pixel = dist;
		}
	};

	class MakeRadiusProcessor:public CircularMaskProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.toradius";
		}
		static Processor *NEW()
		{
			return new MakeRadiusProcessor();
		}

		string get_desc() const
		{
			return "overwrites input, f(x) = radius;";
		}

	  protected:
		void process_dist_pixel(float *pixel, float dist) const
		{
			*pixel = sqrt(dist);
		}
	};

	class ComplexPixelProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		static string get_group_desc()
		{
			return "The base class for fourier space processor working on individual pixels. ri2ap() is called before processing, so individual pixels will be A/P rather than R/I. The processor won't consider the pixel's coordinates and neighbors.";
		}
		
	  protected:
		virtual void process_pixel(float *x) const = 0;
	};

	class ComplexNormPixel:public ComplexPixelProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.complex.normpixels";
		}
		static Processor *NEW()
		{
			return new ComplexNormPixel();
		}

		string get_desc() const
		{
			return "Each Fourier pixel will be normalized. ie - amp=1, phase=unmodified. Useful for performing phase-residual-like computations with dot products.";
		}

	  protected:
		void process_pixel(float *x) const
		{
			*x=1.0;
		}
	};

	class AreaProcessor:public Processor
	{
	  public:
		AreaProcessor():areasize(0), kernel(0), nx(0), ny(0), nz(0)
		{
		}

		void process(EMData * image);

		void set_params(const Dict & new_params)
		{
			params = new_params;
			areasize = params["areasize"];
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("areasize", EMObject::INT);
			return d;
		}

		string get_desc() const
		{
			return "AreaProcessor use pixel values and coordinates of a real-space square area. This is the base class. Specific AreaProcessor needs to implement function create_kernel().";
		}
		
	  protected:
		virtual void process_pixel(float *pixel, float, float, float, float *area_matrix) const
		{
			for (int i = 0; i < matrix_size; i++)
			{
				*pixel += area_matrix[i] * kernel[i];
			}
		}

		virtual void create_kernel() const = 0;

		int areasize;
		int matrix_size;
		float *kernel;
		int nx;
		int ny;
		int nz;
	};

	class LaplacianProcessor:public AreaProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.laplacian";
		}
		static Processor *NEW()
		{
			return new LaplacianProcessor();
		}

		string get_desc() const
		{
			return "Discrete approximation to Laplacian. Edge enchancement, but works poorly in the presence of noise. Laplacian processor (x -> d^2/dx^2 + d^2/dy^2 + d^2/dz^2).";
		}

	  protected:
		void create_kernel() const;

	};

	class ZeroConstantProcessor:public AreaProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.mask.contract";
		}
		static Processor *NEW()
		{
			return new ZeroConstantProcessor();
		}

		string get_desc() const
		{
			return "Contraction of data, if any nearest neighbor is 0, value -> 0, generally used iteratively";
		}
		
	  protected:
		void process_pixel(float *pixel, float, float, float, float *matrix) const
		{
			if (*pixel != 0)
			{
				if (*pixel == matrix[1] || *pixel == matrix[3] || *pixel == matrix[5] ||
					*pixel == matrix[7] || matrix[1] == 0 || matrix[3] == 0 ||
					matrix[5] == 0 || matrix[7] == 0) {
					*pixel = 0;
				}
			}
		}

		void create_kernel() const
		{
		}
	};

	class BoxStatProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		static string get_group_desc()
		{
			return "BoxStatProcessor files are a kind of neighborhood processors. These processors compute every output pixel using information from a reduced region on the neighborhood of the input pixel. The classical form are the 3x3 processors. BoxStatProcessors could perform diverse tasks ranging from noise reduction, to differential , to mathematical morphology. BoxStatProcessor class is the base class. Specific BoxStatProcessor needs to define process_pixel(float *pixel, const float *array, int n).";
		}
		
	  protected:
		virtual void process_pixel(float *pixel, const float *array, int n) const = 0;
	};


	class BoxMedianProcessor:public BoxStatProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.filter.median";
		}
		static Processor *NEW()
		{
			return new BoxMedianProcessor();
		}

		string get_desc() const
		{
			return "A processor for noise reduction. pixel = median of values surrounding pixel.";
		}


	  protected:
		void process_pixel(float *pixel, const float *array, int n) const
		{
			float *data = new float[n];
			memcpy(data, array, sizeof(float) * n);

			for (int i = 0; i <= n / 2; i++)
			{
				for (int j = i + 1; j < n; j++)
				{
					if (data[i] < data[j]) {
						float t = data[i];
						data[i] = data[j];
						data[j] = t;
					}
				}
			}

			if (n % 2 != 0)
			{
				*pixel = data[n / 2];
			}
			else {
				*pixel = (data[n / 2] + data[n / 2 - 1]) / 2;
			}
			if( data )
			{
				delete[]data;
				data = 0;
			}
		}
	};

	class BoxSigmaProcessor:public BoxStatProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.localsigma";
		}
		static Processor *NEW()
		{
			return new BoxSigmaProcessor();
		}

		string get_desc() const
		{
			return "pixel = standard deviation of values surrounding pixel.";
		}

	  protected:
		void process_pixel(float *pixel, const float *data, int n) const
		{
			float sum = 0;
			float square_sum = 0;
			for (int i = 0; i < n; i++)
			{
				sum += data[i];
				square_sum += data[i] * data[i];
			}

			float mean = sum / n;
			*pixel = sqrt(square_sum / n - mean * mean);
		}
	};

	class BoxMaxProcessor:public BoxStatProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.localmax";
		}
		static Processor *NEW()
		{
			return new BoxMaxProcessor();
		}

		string get_desc() const
		{
			return "peak processor: pixel = max of values surrounding pixel.";
		}

	  protected:
		void process_pixel(float *pixel, const float *data, int n) const
		{
			float maxval = -FLT_MAX;
			for (int i = 0; i < n; i++)
			{
				if (data[i] > maxval) {
					maxval = data[i];
				}
			}
			 *pixel = maxval;
		}
	};

	class MinusPeakProcessor:public BoxStatProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.submax";
		}
		static Processor *NEW()
		{
			return new MinusPeakProcessor();
		}

		string get_desc() const
		{
			return "peak processor: pixel = pixel - max of values surrounding pixel. This is a sort of positive peak-finding algorithm.";
		}

	  protected:
		void process_pixel(float *pixel, const float *data, int n) const
		{
			float maxval = -FLT_MAX;
			for (int i = 0; i < n; i++)
			{
				if (data[i] > maxval) {
					maxval = data[i];
				}
			}
			 *pixel -= maxval;
		}
	};

	class PeakOnlyProcessor:public BoxStatProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.mask.onlypeaks";
		}
		static Processor *NEW()
		{
			return new PeakOnlyProcessor();
		}
		void set_params(const Dict & new_params)
		{
			params = new_params;
			npeaks = params["npeaks"];
			if (npeaks == 0) {
				npeaks = 1;
			}
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("npeaks", EMObject::INT);
			return d;
		}

		string get_desc() const
		{
			return "peak processor -> if npeaks or more surrounding values >= value, value->0";
		}

	  protected:
		void process_pixel(float *pixel, const float *data, int n) const
		{
			int r = 0;

			for (int i = 0; i < n; i++)
			{
				if (data[i] >= *pixel) {
					r++;
				}
			}

			if (r > npeaks)
			{
				*pixel = 0;
			}
		}
	  private:
		int npeaks;
	};

	class DiffBlockProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "eman1.filter.blockrange";
		}
		static Processor *NEW()
		{
			return new DiffBlockProcessor();
		}

		string get_desc() const
		{
			return "averages over cal_half_width, then sets the value in a local block";
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("cal_half_width", EMObject::FLOAT);
			d.put("fill_half_width", EMObject::FLOAT);
			return d;
		}
	};

	class CutoffBlockProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "eman1.filter.blockcutoff";
		}
		static Processor *NEW()
		{
			return new CutoffBlockProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("value1", EMObject::FLOAT);
			d.put("value2", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "Block processor, val1 is dx/dy, val2 is lp freq cutoff in pixels. Mystery processor.";
		}
		
	};

	class GradientRemoverProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "eman1.math.lineargradientfix";
		}
		static Processor *NEW()
		{
			return new GradientRemoverProcessor();
		}

		string get_desc() const
		{
			return "Gradient remover, does a rough plane fit to find linear gradients.";
		}
		
	};

	class RampProcessor:public Processor
    {
	  public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "filter.ramp";
		}
		static Processor *NEW()
		{
			return new RampProcessor();
		}

		string get_desc() const
		{
			return "Ramp processor -- Fits a least-squares plane "
				   "to the picture, and subtracts the plane from "
				   "the picture.  A wedge-shaped overall density "
				   "profile can thus be removed from the picture.";
		}
		
	};

	class VerticalStripeProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.math.verticalstripefix";
		}

		static Processor *NEW()
		{
			return new VerticalStripeProcessor();
		}

		string get_desc() const
		{
			return "Tries to fix images scanned on the zeiss for poor ccd normalization.";
		}
		
	};
	
	class RealToFFTProcessor:public Processor
	{
		public:
		void process(EMData *image);
	
		string get_name() const
		{
			return "eman1.math.realtofft";
		}

		static Processor *NEW()
		{
			return new RealToFFTProcessor();
		}

		string get_desc() const
		{
			return "This will replace the image with a full-circle 2D fft amplitude rendering.";
		}
	};
			

	class SigmaZeroEdgeProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.zeroedgefill";
		}
		static Processor *NEW()
		{
			return new SigmaZeroEdgeProcessor();
		}

		string get_desc() const
		{
			return "Fill zeroes at edges with nearest horizontal/vertical value.";
		}
		
	};

	class BeamstopProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.beamstop";
		}

		static Processor *NEW()
		{
			return new BeamstopProcessor();
		}

		string get_desc() const
		{
			return "Try to eliminate beamstop in electron diffraction patterns. value1=sig multiplier; value2,value3 are x,y of center, if value1<0 also does radial subtract.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("value1", EMObject::FLOAT);
			d.put("value2", EMObject::FLOAT);
			d.put("value3", EMObject::FLOAT);
			return d;
		}
	};

	class MeanZeroEdgeProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.dampedzeroedgefill";
		}

		static Processor *NEW()
		{
			return new MeanZeroEdgeProcessor();
		}

		string get_desc() const
		{
			return "Fill zeroes at edges with nearest horizontal/vertical value damped towards Mean2.";
		}
		
	};


	class AverageXProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.math.averageovery";
		}

		static Processor *NEW()
		{
			return new AverageXProcessor();
		}

		string get_desc() const
		{
			return "Average along Y and replace with average";
		}
		
	};

	class ZeroEdgeRowProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		string get_name() const
		{
			return "eman1.mask.zeroedge2d";
		}

		static Processor *NEW()
		{
			return new ZeroEdgeRowProcessor();
		}

		string get_desc() const
		{
			return "zero edges of image on top and bottom, and on left and right.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("x0", EMObject::INT);
			d.put("x1", EMObject::INT);
			d.put("y0", EMObject::INT);
			d.put("y1", EMObject::INT);
			return d;
		}
	};

	class ZeroEdgePlaneProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		string get_name() const
		{
			return "eman1.mask.zeroedge3d";
		}

		static Processor *NEW()
		{
			return new ZeroEdgePlaneProcessor();
		}

		string get_desc() const
		{
			return "zero edges of volume on all sides";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("x0", EMObject::INT);
			d.put("x1", EMObject::INT);
			d.put("y0", EMObject::INT);
			d.put("y1", EMObject::INT);
			d.put("z0", EMObject::INT);
			d.put("z1", EMObject::INT);
			return d;
		}
	};


	class BilateralProcessor:public Processor
	{
	  public:
		void process(EMData * image);
		string get_name() const
		{
			return "eman1.bilateral";
		}

		string get_desc() const
		{
			return "Bilateral processing on 3D volume data. Bilateral processing does non-linear weighted averaging processing within a certain window. ";
		}

		static Processor *NEW()
		{
			return new BilateralProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("distance_sigma", EMObject::FLOAT, "means how large the voxel has impact on its neighbors in spatial domain. The larger it is, the more blurry the resulting image.");
			d.put("value_sigma", EMObject::FLOAT, "means how large the voxel has impact on its in  range domain. The larger it is, the more blurry the resulting image.");
			d.put("niter", EMObject::INT, "how many times to apply this processing on your data.");
			d.put("half_width", EMObject::INT, "processing window size = (2 * half_widthh + 1) ^ 3.");
			return d;
		}
	};

	class NormalizeProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		static string get_group_desc()
		{
			return "Base class for normalization processors. Each specific normalization processor needs to define how to calculate mean and how to calculate sigma.";
		}
		
	  protected:
		virtual float calc_sigma(EMData * image) const;
		virtual float calc_mean(EMData * image) const = 0;
	};

	class NormalizeUnitProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.unitlen";
		}

		static Processor *NEW()
		{
			return new NormalizeUnitProcessor();
		}

		string get_desc() const
		{
			return "Normalize an image so its vector length is 1.0.";
		}

	  protected:
		float calc_sigma(EMData * image) const;
		float calc_mean(EMData * image) const;
	};
	
	inline float NormalizeUnitProcessor::calc_mean(EMData *image) const { return 0; }

	class NormalizeUnitSumProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.unitsum";
		}

		static Processor *NEW()
		{
			return new NormalizeUnitSumProcessor();
		}

		string get_desc() const
		{
			return "Normalize an image so its elements sum to 1.0 (fails if mean=0)";
		}

	  protected:
		float calc_sigma(EMData * image) const;
		float calc_mean(EMData * image) const;
	};
	
	inline float NormalizeUnitSumProcessor::calc_mean(EMData *image) const { return 0; }

		
	class NormalizeStdProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize";
		}

		static Processor *NEW()
		{
			return new NormalizeStdProcessor();
		}

		string get_desc() const
		{
			return "do a standard normalization on an image.";
		}

	  protected:
		float calc_mean(EMData * image) const;
	};

	class NormalizeMaskProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.mask";
		}

		string get_desc() const
		{
			return "Uses a 1/0 mask defining a region to use for the zero-normalization.if no_sigma is 1, standard deviation not modified.";
		}

		static Processor *NEW()
		{
			return new NormalizeMaskProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("mask", EMObject::EMDATA);
			d.put("no_sigma", EMObject::INT);
			return d;
		}

	  protected:
		float calc_sigma(EMData * image) const;
		float calc_mean(EMData * image) const;
	};

	class NormalizeEdgeMeanProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.edgemean";
		}

		static Processor *NEW()
		{
			return new NormalizeEdgeMeanProcessor();
		}

		string get_desc() const
		{
			return "normalizes an image, mean value equals to edge mean.";
		}

	  protected:
		float calc_mean(EMData * image) const;
	};

	class NormalizeCircleMeanProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.circlemean";
		}

		static Processor *NEW()
		{
			return new NormalizeCircleMeanProcessor();
		}

		string get_desc() const
		{
			return "normalizes an image, mean value equals to mean of 2 pixel circular border.";
		}

	  protected:
		float calc_mean(EMData * image) const;
	};

	class NormalizeLREdgeMeanProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.lredge";
		}

		static Processor *NEW()
		{
			return new NormalizeLREdgeMeanProcessor();
		}

		string get_desc() const
		{
			return "normalizes an image, uses 2 pixels on left and right edge";
		}

	  protected:
		float calc_mean(EMData * image) const;
	};

	class NormalizeMaxMinProcessor:public NormalizeProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.maxmin";
		}

		static Processor *NEW()
		{
			return new NormalizeMaxMinProcessor();
		}

		string get_desc() const
		{
			return "normalizes an image. mean -> (maxval-minval)/2; std dev = (maxval+minval)/2;";
		}

	  protected:
		float calc_sigma(EMData * image) const;
		float calc_mean(EMData * image) const;
	};

	class NormalizeRowProcessor:public Processor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.rows";
		}

		static Processor *NEW()
		{
			return new NormalizeRowProcessor();
		}

		string get_desc() const
		{
			return "normalizes each row in the image individually";
		}

		void process(EMData * image);
	};

	class NormalizeToStdProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.normalize.toimage";
		}

		static Processor *NEW()
		{
			return new NormalizeToStdProcessor();
		}

		string get_desc() const
		{
			return "multiply 'this' by a constant so it is scaled to the signal in 'to'.keepzero will exclude zero values, and keep them at zero in the result.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("noisy", EMObject::EMDATA);
			d.put("keepzero", EMObject::INT);
			d.put("invert", EMObject::INT);
			d.put("mult", EMObject::FLOAT);
			d.put("add", EMObject::FLOAT);
			return d;
		}
	};

	class NormalizeToFileProcessor:public NormalizeToStdProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.normalize.tofile";
		}

		static Processor *NEW()
		{
			return new NormalizeToFileProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("noisyfile", EMObject::STRING);
			d.put("keepzero", EMObject::INT, "exclude zero values");
			d.put("invert", EMObject::INT);
			d.put("mult", EMObject::FLOAT);
			d.put("add", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "Multiply this image by a constant so it is scaled to the signal in 'noisyfile'";
		}
		
	};


	class NormalizeToLeastSquareProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.normalize.toimage.lsq";
		}

		static Processor *NEW()
		{
			return new NormalizeToLeastSquareProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("to", EMObject::EMDATA);
			d.put("low_threshold", EMObject::FLOAT);
			d.put("high_threshold", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "use least square method to normalize";
		}
		
	};

	class RadialAverageProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.math.radialaverage";
		}

		static Processor *NEW()
		{
			return new RadialAverageProcessor();
		}

		string get_desc() const
		{
			return "makes image circularly symmetric.";
		}
		
	};

	class RadialSubstractProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.math.radialsubtract";
		}

		static Processor *NEW()
		{
			return new RadialSubstractProcessor();
		}

		string get_desc() const
		{
			return "subtracts circularly symmetric part of an image.";
		}
		
	};


	class FlipProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.xform.flip";
		}

		static Processor *NEW()
		{
			return new FlipProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("axis", EMObject::STRING, "'x', 'y', or 'z' axis. 'x' means horizonal flip; 'y' means vertical flip;");
			return d;
		}

		string get_desc() const
		{
			return "flip an image around an axis.";
		}
		
	};

	class AddNoiseProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.math.addnoise";
		}

		static Processor *NEW()
		{
			return new AddNoiseProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("noise", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "add noise to an image";
		}

	  protected:
		virtual float get_sigma(EMData *)
		{
			return 1.0;
		}
	};

	class AddSigmaNoiseProcessor:public AddNoiseProcessor
	{
	  public:
		string get_name() const
		{
			return "eman1.math.addsignoise";
		}

		static Processor *NEW()
		{
			return new AddSigmaNoiseProcessor();
		}

		string get_desc() const
		{
			return "add sigma noise.";
		}
		
	  protected:
		float get_sigma(EMData * image);
	};


	class AddRandomNoiseProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.addspectralnoise";
		}

		static Processor *NEW()
		{
			return new AddRandomNoiseProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("n", EMObject::INT);
			d.put("x0", EMObject::FLOAT);
			d.put("dx", EMObject::FLOAT);
			d.put("y", EMObject::FLOATARRAY);
			d.put("interpolation", EMObject::INT);
			return d;
		}

		string get_desc() const
		{
			return "add random noise.";
		}

	};

	class FourierOriginShiftProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.xform.fourierorigin";
		}

		static Processor *NEW()
		{
			return new FourierOriginShiftProcessor();
		}
		
		string get_desc() const
		{
			return "Translates the origin in Fourier space from the corner to the center in Y";
		}

	};
	
	class Phase180Processor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.xform.phaseorigin";
		}

		static Processor *NEW()
		{
			return new Phase180Processor();
		}
		
		string get_desc() const
		{
			return "Translates a centered image to the corner";
		}

	};

	class AutoMask2DProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.auto2d";
		}

		static Processor *NEW()
		{
			return new AutoMask2DProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("threshold", EMObject::FLOAT, "runs from ~ -2 to 2, negative numbers for dark protein and positive numbers for light protein (stain).");
			d.put("filter", EMObject::FLOAT, "is expressed as a fraction of the fourier radius.");
			return d;
		}
		
		string get_desc() const
		{
			return "Attempts to automatically mask out the particle, excluding other particles in the box, etc.";
		}

	};

	class AutoMask3DProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.auto3d.thresh";
		}

		static Processor *NEW()
		{
			return new AutoMask3DProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("threshold1", EMObject::FLOAT);
			d.put("threshold2", EMObject::FLOAT);
			return d;
		}

		string get_desc() const
		{
			return "Tries to mask out only interesting density";
		}

		static void search_nearby(float *dat, float *dat2, int nx, int ny, int nz, float thr);
		static void fill_nearby(float *dat2, int nx, int ny, int nz);
	};

	class AutoMask3D2Processor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.auto3d";
		}

		static Processor *NEW()
		{
			return new AutoMask3D2Processor();
		}

		string get_desc() const
		{
			return "Tries to mask out only interesting density";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("radius", EMObject::INT);
			d.put("threshold", EMObject::FLOAT);
			d.put("nshells", EMObject::INT);
			return d;
		}
	};

	class AddMaskShellProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.addshells";
		}

		string get_desc() const
		{
			return "Add additional shells/rings to an existing 1/0 mask image";
		}

		static Processor *NEW()
		{
			return new AddMaskShellProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("nshells", EMObject::INT, "number of shells to add");
			return d;
		}
	};

	class ToMassCenterProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.xform.centerofmass";
		}

		static Processor *NEW()
		{
			return new ToMassCenterProcessor();
		}

		string get_desc() const
		{
			return "ToMassCenterProcessor centers image at center of mass, ignores old dx, dy.";
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("int_shift_only", EMObject::INT);
			return d;
		}
	};

	class ACFCenterProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.xform.centeracf";
		}

		static Processor *NEW()
		{
			return new ACFCenterProcessor();
		}

		string get_desc() const
		{
			return "Center image using CCF with 180 degree rotation.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("is3d", EMObject::INT);
			return d;
		}
	};

	class SNRProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.filter.snr";
		}

		static Processor *NEW()
		{
			return new SNRProcessor();
		}

		string get_desc() const
		{
			return "Processor the images by the estimated SNR in each image.if parameter 'wiener' is 1, then wiener processor the images using the estimated SNR with CTF amplitude correction.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("wiener", EMObject::INT);
			d.put("snrfile", EMObject::STRING);
			return d;
		}
	};

	class FileFourierProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.filter.byfile";
		}

		string get_desc() const
		{
			return "A fourier processor specified in a 2 column text file.";
		}

		static Processor *NEW()
		{
			return new FileFourierProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("filename", EMObject::STRING);
			return d;
		}
	};

	/** Identifiy the best symmetry in the given symmetry list for each pixel and then apply the best symmetry to each pixel
	 *
	 * @author Wen Jiang <wjiang@bcm.tmc.edu> 
	 * @date 2005-1-9
	 * @param sym[in] the list of symmetries to search
	 * @param thresh[in] the minimal level of symmetry to be accepted (0-1)
	 * @param output_symlabel[in] if output the symmetry label map in which the pixel value is the index of symmetry in the symmetry list
	 * @param symlabel_map[out] the optional return map when output_symlabel=1
	 */

	class SymSearchProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.misc.symsearch";
		}

		string get_desc() const
		{
			return "Identifiy the best symmetry in the given symmetry list for each pixel and then apply the best symmetry to each pixel.";
		}

		static Processor *NEW()
		{
			return new SymSearchProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sym", EMObject::STRINGARRAY, "the list of symmetries to search");
			d.put("thresh", EMObject::FLOAT, "the minimal level of symmetry to be accepted (0-1)");
			d.put("output_symlabel", EMObject::INT, "if output the symmetry label map in which the pixel value is the index of symmetry in the symmetry list");
			d.put("symlabel_map", EMObject::EMDATA, "the optional return map when output_symlabel=1");
			return d;
		}
	};

	class LocalNormProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.misc.localnorm";
		}

		static Processor *NEW()
		{
			return new LocalNormProcessor();
		}

		string get_desc() const
		{
			return "This processor attempts to perform a 'local normalization' so low density and high density features will be on a more even playing field in an isosurface display. threshold is an isosurface threshold at which all desired features are visible, radius is a normalization size similar to an lp= value.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("threshold", EMObject::FLOAT);
			d.put("radius", EMObject::FLOAT);
			d.put("apix", EMObject::FLOAT);
			return d;
		}
	};

	class IndexMaskFileProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.fromfile";
		}

		static Processor *NEW()
		{
			return new IndexMaskFileProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("filename", EMObject::STRING);
			d.put("ismaskset", EMObject::INT);
			return d;
		}

		string get_desc() const
		{
			return "Multiplies the image by the specified file using pixel indices. The images must be same size. If 'ismaskset=' is 1, it will take a file containing a set of masks and apply the first mask to the image.";
		}

	};

	class CoordinateMaskFileProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.fromfile.sizediff";
		}

		static Processor *NEW()
		{
			return new CoordinateMaskFileProcessor();
		}

		string get_desc() const
		{
			return "Multiplies the image by the specified file using pixel coordinates instead of pixel indices. The images can be different size.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("filename", EMObject::STRING);
			return d;
		}
	};

	class SetSFProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.misc.setpowspec";
		}

		string get_desc() const
		{
			return "Sets the structure factor based on a 1D x/y text file.";
		}

		static Processor *NEW()
		{
			return new SetSFProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("filename", EMObject::STRING);
			return d;
		}
	};

	class SmartMaskProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.smart";
		}

		static Processor *NEW()
		{
			return new SmartMaskProcessor();
		}

		string get_desc() const
		{
			return "Smart mask processor.";
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("mask", EMObject::FLOAT);
			return d;
		}
	};

	class IterBinMaskProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.mask.addshells.gauss";
		}

		string get_desc() const
		{
			return "Iterative expansion of a binary mask, val1 is number of pixels to expand, if val2!=0 will make a soft Gaussian edge starting after val2 pixels.";
		}

		static Processor *NEW()
		{
			return new IterBinMaskProcessor();
		}

		TypeDict get_param_types() const
		{
			TypeDict d;
			return d;
		}
	};

	class TestImageProcessor : public Processor
	{
	public:
		static string get_group_desc()
		{
			return "This is a group of 'processor' used to create test image.";
		}
	
	protected:
		void preprocess(const EMData * const image);
		int nx, ny, nz; //this is the size of the source image
	};
	
	class TestImagePureGaussian : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.puregaussian";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a strict Gaussian ";
		}
		
		static Processor * NEW()
		{
			return new TestImagePureGaussian();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "sigma value for this Gaussian blob");
			return d;
		}
	};
	
	class TestImageGaussian : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.gaussian";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a Gaussian Blob";
		}
		
		static Processor * NEW()
		{
			return new TestImageGaussian();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("sigma", EMObject::FLOAT, "sigma value for this Gaussian blob");
			d.put("axis", EMObject::STRING, "specify a major axis for asymmetric features");
			d.put("c", EMObject::FLOAT, "distance between focus and the center of an ellipse");
			return d;
		}
	};
	
	class TestImageScurve : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.scurve";
		}
		
		string get_desc() const
		{
			return "Replace a source image with a lumpy S-curve used for alignment testing";
		}
		
		static Processor * NEW()
		{
			return new TestImageScurve();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			return d;
		}
	};
	
	class TestImageSinewave : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.sinewave";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a sine wave in specified wave length";
		}
		
		static Processor * NEW()
		{
			return new TestImageSinewave();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("wave_length", EMObject::FLOAT, "this value is the d in function |sin(x/d)|");
			d.put("axis", EMObject::STRING, "specify a major axis for asymmetric features");
			d.put("c", EMObject::FLOAT, "distance between focus and the center of an ellipse");
			d.put("phase", EMObject::FLOAT, "(optional)phase for sine wave, default is 0");
			return d;
		}
	};
	
	class TestImageSquarecube : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.squarecube";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a square or cube depends on 2D or 3D of the source image";
		}
		
		static Processor * NEW()
		{
			return new TestImageSquarecube();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("edge_length", EMObject::FLOAT, "edge length of the square or cube");
			d.put("axis", EMObject::STRING, "specify a major axis for asymmetric features");
			d.put("odd_edge", EMObject::FLOAT, "edge length for the asymmetric axis");
			d.put("fill", EMObject::STRING, "answer 'yes' or 'no' to specify if it's filled or hollow, default filled");
			return d;
		}
	};
	
	class TestImageCirclesphere : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.circlesphere";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a circle or sphere depends on 2D or 3D of the source image";
		}
		
		static Processor * NEW()
		{
			return new TestImageCirclesphere();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("radius", EMObject::FLOAT, "radius of circle or sphere");
			d.put("axis", EMObject::STRING, "specify a major axis for asymmetric features");
			d.put("c", EMObject::FLOAT, "distance between focus and the center of an ellipse");
			d.put("fill", EMObject::STRING, "answer 'yes' or 'no' to specify if it's filled or hollow, default filled");
			return d;
		}
	};
	
	class TestImageNoiseUniformRand : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.noise.uniform.rand";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a uniform random noise, random number generated from rand(), the pixel value is from 0 to 1";
		}
		
		static Processor * NEW()
		{
			return new TestImageNoiseUniformRand();
		}
	};
	
	class TestImageNoiseGauss : public TestImageProcessor
	{
	public:
		void process(EMData * image);
		
		string get_name() const
		{
			return "testimage.noise.gauss";
		}
		
		string get_desc() const
		{
			return "Replace a source image as a random noise, the random value is gaussian distributed";
		}
		
		static Processor * NEW()
		{
			return new TestImageNoiseGauss();
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			d.put("noise_level", EMObject::FLOAT, "sigma value of gausian distributed noise, this parameter is optional default is 0.5");
			return d;
		}
	};

#if 0

	class XYZProcessor:public Processor
	{
	  public:
		void process(EMData * image);

		string get_name() const
		{
			return "eman1.XYZ";
		}

		static Processor *NEW()
		{
			return new XYZProcessor();
		}

		string get_desc() const
		{
			return "N/A";
		}
		
		TypeDict get_param_types() const
		{
			TypeDict d;
			return d;
		}
	};


#endif


	int multi_processors(EMData * image, vector < string > processornames);
	void dump_processors();
	map<string, vector<string> > group_processors();

	template <> Factory < Processor >::Factory();
}

#endif	//eman_filter_h__

/* vim: set ts=4 noet: */
