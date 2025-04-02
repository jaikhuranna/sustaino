//
//  ProductDetailsViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 10/03/25.
//

import UIKit

class ProductDetailsViewController: UIViewController {
    
    public static var productImage: UIImage?
    public static var jason: String?

    var productDetails: DataModel.ProductDetails?
    var alternativeProduct: DataModel.AlternativeProduct?
    var diyIdeas: [DataModel.DIYIdea] = []

    @IBOutlet var tunharaTExt: UILabel!
    @IBOutlet var ProductUIimageView: UIImageView!

    override func viewDidLoad() {
        super.viewDidLoad()

        ProductUIimageView.layer.cornerRadius = 16
        ProductUIimageView.image = HomeViewController.capturedImage
        ProductDetailsViewController.productImage = ProductUIimageView.image

        if let details = productDetails {
            displayStructuredProductDetails(details)
        } else {
            tunharaTExt.text = DataModel.productDetails?.description
//            tunharaTExt.text = ProductDetailsViewController.jason ?? "A popular carbonated soft drink containing high amounts of sugar and caffeine, contributing to a lower health score. The product comes in a plastic bottle, which has a moderate sustainability score due to its recyclability but contributes to plastic waste."
        }
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)

        print("✅ Product Details in View: \(String(describing: productDetails))")

        if let details = productDetails {
            displayStructuredProductDetails(details)
        } else {
            tunharaTExt.text = DataModel.productDetails?.description
//            tunharaTExt.text = ProductDetailsViewController.jason ?? "A popular carbonated soft drink containing high amounts of sugar and caffeine, contributing to a lower health score. The product comes in a plastic bottle, which has a moderate sustainability score due to its recyclability but contributes to plastic waste."
        }
    }

    
    @IBAction func tapRescan(_ sender: Any) {
        dismiss(animated: true)
    }

    func displayStructuredProductDetails(_ details: DataModel.ProductDetails) {
        let formattedText = """
        Product Name: \(details.name)
        
        Description: \(details.description)
        
        Health Score: \(details.healthScore)/100
        Sustainability Score: \(details.sustainabilityScore)/100
        """

        tunharaTExt.text = formattedText
    }
}
