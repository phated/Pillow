import pytest
from PIL import Image, WebPImagePlugin

from .helper import (
    assert_image_similar,
    assert_image_similar_tofile,
    hopper,
    skip_unless_feature,
)

try:
    from PIL import _webp

    HAVE_WEBP = True
except ImportError:
    HAVE_WEBP = False


class TestUnsupportedWebp:
    def test_unsupported(self):
        if HAVE_WEBP:
            WebPImagePlugin.SUPPORTED = False

        file_path = "Tests/images/hopper.webp"
        pytest.warns(UserWarning, lambda: pytest.raises(IOError, Image.open, file_path))

        if HAVE_WEBP:
            WebPImagePlugin.SUPPORTED = True


@skip_unless_feature("webp")
class TestFileWebp:
    def setup_method(self):
        self.rgb_mode = "RGB"

    def test_version(self):
        _webp.WebPDecoderVersion()
        _webp.WebPDecoderBuggyAlpha()

    def test_read_rgb(self):
        """
        Can we read a RGB mode WebP file without error?
        Does it have the bits we expect?
        """

        with Image.open("Tests/images/hopper.webp") as image:
            assert image.mode == self.rgb_mode
            assert image.size == (128, 128)
            assert image.format == "WEBP"
            image.load()
            image.getdata()

            # generated with:
            # dwebp -ppm ../../Tests/images/hopper.webp -o hopper_webp_bits.ppm
            assert_image_similar_tofile(image, "Tests/images/hopper_webp_bits.ppm", 1.0)

    def test_write_rgb(self, tmp_path):
        """
        Can we write a RGB mode file to webp without error.
        Does it have the bits we expect?
        """

        temp_file = str(tmp_path / "temp.webp")

        hopper(self.rgb_mode).save(temp_file)
        with Image.open(temp_file) as image:
            assert image.mode == self.rgb_mode
            assert image.size == (128, 128)
            assert image.format == "WEBP"
            image.load()
            image.getdata()

            # generated with: dwebp -ppm temp.webp -o hopper_webp_write.ppm
            assert_image_similar_tofile(
                image, "Tests/images/hopper_webp_write.ppm", 12.0
            )

            # This test asserts that the images are similar. If the average pixel
            # difference between the two images is less than the epsilon value,
            # then we're going to accept that it's a reasonable lossy version of
            # the image. The old lena images for WebP are showing ~16 on
            # Ubuntu, the jpegs are showing ~18.
            target = hopper(self.rgb_mode)
            assert_image_similar(image, target, 12.0)

    def test_write_unsupported_mode_L(self, tmp_path):
        """
        Saving a black-and-white file to WebP format should work, and be
        similar to the original file.
        """

        temp_file = str(tmp_path / "temp.webp")
        hopper("L").save(temp_file)
        with Image.open(temp_file) as image:
            assert image.mode == self.rgb_mode
            assert image.size == (128, 128)
            assert image.format == "WEBP"

            image.load()
            image.getdata()
            target = hopper("L").convert(self.rgb_mode)

            assert_image_similar(image, target, 10.0)

    def test_write_unsupported_mode_P(self, tmp_path):
        """
        Saving a palette-based file to WebP format should work, and be
        similar to the original file.
        """

        temp_file = str(tmp_path / "temp.webp")
        hopper("P").save(temp_file)
        with Image.open(temp_file) as image:
            assert image.mode == self.rgb_mode
            assert image.size == (128, 128)
            assert image.format == "WEBP"

            image.load()
            image.getdata()
            target = hopper("P").convert(self.rgb_mode)

            assert_image_similar(image, target, 50.0)

    def test_WebPEncode_with_invalid_args(self):
        """
        Calling encoder functions with no arguments should result in an error.
        """

        if _webp.HAVE_WEBPANIM:
            with pytest.raises(TypeError):
                _webp.WebPAnimEncoder()
        with pytest.raises(TypeError):
            _webp.WebPEncode()

    def test_WebPDecode_with_invalid_args(self):
        """
        Calling decoder functions with no arguments should result in an error.
        """

        if _webp.HAVE_WEBPANIM:
            with pytest.raises(TypeError):
                _webp.WebPAnimDecoder()
        with pytest.raises(TypeError):
            _webp.WebPDecode()

    def test_no_resource_warning(self, tmp_path):
        file_path = "Tests/images/hopper.webp"
        with Image.open(file_path) as image:
            temp_file = str(tmp_path / "temp.webp")
            pytest.warns(None, image.save, temp_file)

    def test_file_pointer_could_be_reused(self):
        file_path = "Tests/images/hopper.webp"
        with open(file_path, "rb") as blob:
            Image.open(blob).load()
            Image.open(blob).load()

    @skip_unless_feature("webp")
    @skip_unless_feature("webp_anim")
    def test_background_from_gif(self, tmp_path):
        with Image.open("Tests/images/chi.gif") as im:
            original_value = im.convert("RGB").getpixel((1, 1))

            # Save as WEBP
            out_webp = str(tmp_path / "temp.webp")
            im.save(out_webp, save_all=True)

        # Save as GIF
        out_gif = str(tmp_path / "temp.gif")
        Image.open(out_webp).save(out_gif)

        with Image.open(out_gif) as reread:
            reread_value = reread.convert("RGB").getpixel((1, 1))
        difference = sum(
            [abs(original_value[i] - reread_value[i]) for i in range(0, 3)]
        )
        assert difference < 5
