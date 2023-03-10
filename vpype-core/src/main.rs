use std::f64::consts::PI;


type Complex = num::complex::Complex64;

trait Segment: Sized { // sized needed for the ownership of self in default methods
    fn start(&self) -> Complex;
    fn end(&self) -> Complex;

    // transforms
    fn translate(self, x: f64, y: f64) -> Self;
    fn rotate_complex(self, cis: Complex) -> Self;
    fn rotate(self, angle: f64) -> Self {
        self.rotate_complex(Complex::new(angle.cos(), angle.sin()))
    }
    fn scale(self, factor: Complex) -> Self;
}


#[derive(Debug)]
struct QuadraticBezierSegment {
    first: Complex,
    control: Complex,
    last: Complex,
}

impl Segment for QuadraticBezierSegment {
    fn start(&self) -> Complex {
        self.first
    }

    fn end(&self) -> Complex {
        self.last
    }

    fn translate(self, x: f64, y: f64) -> Self {
        let offset = Complex::new(x, y);
        QuadraticBezierSegment {
            first: self.first + offset,
            control: self.control + offset,
            last: self.last + offset,
        }
    }

    fn rotate_complex(self, cis: Complex) -> Self {
        QuadraticBezierSegment {
            first: self.first * cis,
            control: self.control * cis,
            last: self.last * cis,
        }
    }

    fn scale(self, factor: Complex) -> Self {
        QuadraticBezierSegment {
            first: Complex::new(self.first.re * factor.re, self.first.im * factor.im),
            control: Complex::new(self.control.re * factor.re, self.control.im * factor.im),
            last: Complex::new(self.last.re * factor.re, self.last.im * factor.im),
        }
    }
}

fn main() {
    let q = QuadraticBezierSegment {
        first: Complex::new(0.0, 0.0),
        control: Complex::new(1.0, 1.0),
        last: Complex::new(2.0, 2.0),
    };

    println!("Hello, world!{:?}", q);

    let q2 = q.rotate(0.5 * PI);

    println!("q2 = {:?}", q2);
}
