//
//  AltViewController.swift
//  Sustano
//
//  Created by Jai Khurana on 11/03/25.
//

import UIKit

class AltViewController: UIViewController {
    @IBOutlet var descriptionLabel: UILabel!
    
    var alternativeProduct: DataModel.AlternativeProduct?
    @IBOutlet var productnamelbel: UILabel!
    override func viewDidLoad() {
        super.viewDidLoad()

        productnamelbel.text = alternativeProduct?.productName
        descriptionLabel.text = alternativeProduct?.reason
        
        
        
    }
    

    /*
    // MARK: - Navigation

    // In a storyboard-based application, you will often want to do a little preparation before navigation
    override func prepare(for segue: UIStoryboardSegue, sender: Any?) {
        // Get the new view controller using segue.destination.
        // Pass the selected object to the new view controller.
    }
    */

}
